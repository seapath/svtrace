import argparse
import pyshark
import subprocess
import configparser
import importlib.resources as pkg_resources
import seapath_trace

def live():
    process = run_command("live")

    try:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        stderr_output = process.stderr.read()
        if stderr_output:
            print(stderr_output.strip())

    except KeyboardInterrupt:
        print("\033[0m")
        print("Exiting...")
        process.terminate()
    finally:
        process.wait()

def record():
    output = ''
    process = run_command("record")

    try:
        print("Start recording. Hit CTRL + C to stop")
        while True:
            output = process.stdout.readline() + output
            if output == '' and process.poll() is not None:
                break

        stderr_output = process.stderr.read()
        if stderr_output:
            print(stderr_output.strip())

    except KeyboardInterrupt:
        f = open(f"{args.out}results", "w")
        f.write(output.strip())
        f.close()

        print(f"Results saved to {args.out}results")
        print("Exiting...")
        process.terminate()
    finally:
        process.wait()

def run_command(command):
    sv_id, sv_counter = extract_sv_fields()
    sum_sv_id = sum([ord(char) for char in sv_id])

    try:
        bpf_script_path = pkg_resources.files(seapath_trace).joinpath(f'{command}.bt')
    except FileNotFoundError as e:
        print(f"Fatal: required bpftrace script for {command} command not found")
        exit(1)

    if args.machine == 'hypervisor':
        sv_irq_pid = get_pid(sv_interface)
        qemu_pid = get_pid("qemu")
        bpftrace_cmd = f"export BPFTRACE_MAX_MAP_KEYS=100000 && chrt -f 1 bpftrace --unsafe {bpf_script_path} \
            {len(sv_id)} \
            {sum_sv_id} \
            {sv_counter.pos} \
            {sv_irq_pid} \
            {qemu_pid}"

    elif args.machine == 'VM':
        virtio_input_pid = extract_virtio_pid()

        bpftrace_cmd = f"export BPFTRACE_MAX_MAP_KEYS=100000 && chrt -f 1 bpftrace --unsafe {bpf_script_path} \
            {len(sv_id)} \
            {sum_sv_id} \
            {sv_counter.pos} \
            {virtio_input_pid} \
            {virtio_input_pid}"

    process = subprocess.Popen(
        bpftrace_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return process


def extract_sv_fields():
    capture = pyshark.LiveCapture(interface=f'{sv_interface}')
    packet = None
    print("Waiting for SV...")
    for packet in capture.sniff_continuously():
        if packet.highest_layer == 'SV':
            break

    sv_id =  packet.sv.svID
    sv_counter = packet.sv.smpCnt
    print(f"Detected SV stream: {sv_id}")
    return sv_id, sv_counter

def extract_virtio_pid():
# In the context of VM using virtio driver, the SV interface name is
# not the same as the IRQ process name (ex: enp0s9 != irq/29-virtio3...)
# To bypass this, we need, from the interface name, to make the correlation
# between it and the process name.

    if args.machine == 'VM':
        # Grab the SV interface PCI bus
        ethtool_cmd = f"ethtool -i {sv_interface}|grep \"bus-info\"| awk '{{print $2}}'"
        try:
           result = subprocess.run(
                ethtool_cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error while running {ethtool_cmd}")
            print(e.stderr)
            exit(1)

        virtio_pci_bus = str.rstrip(result.stdout) # Ex: 0000:00:09.0

        # With it, getting the IRQ number associate to it
        interrupt_cmd = f"grep -E \'{virtio_pci_bus}.*input\' /proc/interrupts | awk '{{print $1}}'"

        try:
           result = subprocess.run(
                interrupt_cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Error while running {interrupt_cmd}")
            print(e.stderr)
            exit(1)

        virtio_input_irq_number  = str.rstrip(result.stdout) # Ex: 29:
        virtio_input_irq_number = virtio_input_irq_number.replace(':', '') # Ex: 29

        # Finally getting process name of the IRQ associate to it
        virtio_input_pid = get_pid(f"irq/{virtio_input_irq_number}") # IRQ/29-virtio...

        return virtio_input_pid

    else:
        sv_irq_pid = get_pid(sv_interface)
        qemu_pid = get_pid("qemu")

        return sv_irq_pid, qemu_pid

def get_pid(process):
    cmd = f"pgrep \"{process}\" | head -n1"

    pgrep_process = []

    try:
        pgrep_process = (subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ))
    except subprocess.CalledProcessError as e:
        print(f"Error while running {cmd}")
        print(e.stderr)
        exit(1)

    try:
        pid = int(pgrep_process.stdout)
    except ValueError as e:
        print(f"Fatal: Required PID process {process} not found")
        exit(1)
    return pid

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="seapath-trace - seapath-trace is a tool used to monitor IEC61850 SV network performance on a machine.")
    group = parser.add_mutually_exclusive_group()

    group.add_argument("--live",action='store_true', help="Show live latency distribution. Default program behavior.")
    group.add_argument("--record",action='store_true', help="Record latency in file results")
    parser.add_argument("--machine", required=True, choices=["hypervisor", "VM"], help="Type of machine seapath-trace is being executed (hypervisor/VM)")

    parser.add_argument("--conf", required=True, help="Path to seapath-trace.cfg configuration file")
    parser.add_argument("--out", default="/tmp/", help="Output results file for --record option")

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.conf)
    sv_interface = config.get('DEFAULT','SV_INTERFACE')

    if args.record:
        record()
    else:
        live()
