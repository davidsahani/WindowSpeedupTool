import datetime
import platform
from collections import OrderedDict

import wmi

C = wmi.WMI()


def processor() -> list[tuple[str, str | int]]:
    "Return processor information."

    cpu = C.Win32_Processor()[0]
    cs = C.Win32_ComputerSystem()[0]
    model, manufacturer = platform.processor().split(',')
    info = [
        ("Name", cpu.Name),
        ("Model", model),
        ("Manufacturer", manufacturer.strip()),
        ("Architecture", cpu.Architecture),
        ("Cores", cpu.NumberOfCores),
        ("Threads", cpu.NumberOfLogicalProcessors),
        ("Sockets", cs.NumberOfProcessors),
        ("Socket name", cpu.SocketDesignation),
        ("Max frequency", f"{cpu.MaxClockSpeed} mhz"),
    ]
    for num, cache in enumerate(C.Win32_CacheMemory(), start=1):
        info.append((f"L{num} Cache", f"{cache.InstalledSize} Kb"))
    return info


def gpus() -> OrderedDict[str, list[tuple[str, str]]]:
    "Return gpus information."

    info: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()

    for gpu in C.Win32_VideoController():
        info[gpu.DeviceID] = [
            ("DeviceID", gpu.DeviceID),
            ("Name", gpu.Name),
            ("Caption", gpu.Caption),
            ("DriverVersion", gpu.DriverVersion),
            ("VideoProcessor", gpu.VideoProcessor),
            ("AdapterRam", f"{(gpu.AdapterRAM or 0) / 10 ** 9} GB"),
            ("Current RefreshRate", f"{gpu.CurrentRefreshRate} Hz"),
            ("Current Resolution",
             f"{gpu.CurrentHorizontalResolution} x {gpu.CurrentVerticalResolution}"),

            ("AdapterDACType", gpu.AdapterDACType),
            ("Availability", gpu.Availability),
            ("AdapterCompatibility", gpu.AdapterCompatibility),
            ("CurrentScanMode", gpu.CurrentScanMode),
            ("CurrentBitsPerPixel", gpu.CurrentBitsPerPixel),
            ("CurrentNumberOfColors", gpu.CurrentNumberOfColors),
        ]
    return info


def rams() -> OrderedDict[str, list[tuple[str, str]]]:
    "Return rams information."

    info: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()

    for memory in C.Win32_PhysicalMemory():
        info[memory.DeviceLocator] = [
            ("DeviceLocator", memory.DeviceLocator),
            ("Type", memory.MemoryType),
            ("Capacity", f"{int(memory.Capacity or 0) / 10 ** 9} GB"),
            ("Speed", f"{memory.Speed} Mhz"),
            ("ConfiguredClockSpeed", f"{memory.ConfiguredClockSpeed} Mhz"),
            ("ConfiguredVoltage", f"{memory.ConfiguredVoltage} mV"),
            ("DataWidth", f"{memory.DataWidth} bits"),
            ("InterleaveDataDepth", memory.InterleaveDataDepth),
            ("InterleavePosition", memory.InterleavePosition),

            ("Manufacturer", memory.Manufacturer),
            ("FormFactor", memory.FormFactor),
            ("Part Number", memory.PartNumber.strip()),
            ("SerialNumber", memory.SerialNumber),
            ("Tag", memory.Tag),
        ]
    return info


def disks() -> OrderedDict[str, list[tuple[str, str]]]:
    "Return disks information."

    info: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()

    for disk in C.Win32_DiskDrive():
        info[disk.Model] = [
            ("Model", disk.Model),
            ("Status", disk.Status),
            ("Size", f"{int(disk.Size or 0) / 10 ** 9} GB"),
            ("Interface Type", disk.InterfaceType),
            ("Media Type", disk.MediaType),
            ("Partitions", disk.Partitions),
            ("Serial Number", disk.SerialNumber.strip()),
        ]
    return info


def net_adapters() -> OrderedDict[str, list[tuple[str, str]]]:
    "Return network adapters information."

    info: OrderedDict[str, list[tuple[str, str]]] = OrderedDict()

    for adapter in C.Win32_NetworkAdapter():
        info[adapter.Name] = [
            ("Name", adapter.Name),
            ("Description", adapter.Description),
            ("MAC Address", adapter.MACAddress),
            ("Net Connection ID", adapter.NetConnectionID),
            ("Speed", f"{int(adapter.Speed or 0) / 1000000} mbps"),
            ("AdapterType", adapter.AdapterType),
            ("PNPDeviceID", adapter.PNPDeviceID),
            ("Manufacturer", adapter.Manufacturer),
            ("ProductName", adapter.ProductName),
            ("MaxNumberControlled", adapter.MaxNumberControlled),
            ("AdapterTypeID", adapter.AdapterTypeID),
        ]
    return info


def motherboard() -> list[tuple[str, str | int]]:
    "Return motherboard information."

    board = C.Win32_BaseBoard()[0]
    return [
        ("Manufacturer", board.Manufacturer),
        ("Product", board.Product),
        ("Serial Number", board.SerialNumber),
        ("Version", board.Version),
        ("Part Number", board.PartNumber),
        # ("Product Name:", board.ProductName),
        # ("PnP Device ID:", board.PNPDeviceID)
    ]


def os_info() -> list[tuple[str, str]]:
    "Return windows os information."

    os = C.Win32_OperatingSystem()[0]
    date_str, time_str = os.InstallDate.split('.')
    install_date = datetime.datetime.strptime(date_str, '%Y%m%d%H%M%S')
    install_date += datetime.timedelta(minutes=int(time_str[-3:]))
    formatted_install_date = install_date.strftime('%Y-%m-%d %H:%M:%S')

    return [
        ("Name", os.Name.split('|', maxsplit=1)[0]),
        ("version", os.Version),
        ("Build", os.BuildNumber),
        ("Machine", platform.machine()),
        ("Architecture", os.OSArchitecture),
        ("Host Name", platform.node()),
        ("Service Pack Minor Version", os.ServicePackMinorVersion),
        ("Service Pack Major Version", os.ServicePackMajorVersion),
        ("Install Date", formatted_install_date),
        ("Registered User", os.RegisteredUser),
    ]
    ("Total Visible Memory Size:", os.TotalVisibleMemorySize, "bytes"),
    ("Free Physical Memory:", os.FreePhysicalMemory, "bytes"),
    ("Total Virtual Memory Size:", os.TotalVirtualMemorySize, "bytes"),
    ("Free Virtual Memory:", os.FreeVirtualMemory, "bytes"),
