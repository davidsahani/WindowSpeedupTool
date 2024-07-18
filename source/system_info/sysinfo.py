# pyright: basic
import datetime
import platform

import wmi

C = wmi.WMI()


def processor() -> list[tuple[str, str | int | bool]]:
    "Return processor information."

    cpu = C.Win32_Processor()[0]
    info = [
        ("Name", cpu.Name),
        ("Description", cpu.Description),
        ("Manufacturer", cpu.Manufacturer),
        ("CurrentClockSpeed", f"{cpu.CurrentClockSpeed} Mhz"),
        ("MaxClockSpeed", f"{cpu.MaxClockSpeed} Mhz"),
        ("Cores", f"{cpu.NumberOfCores}, Threads: {cpu.ThreadCount}"),
        ("LogicalProcessors", cpu.NumberOfLogicalProcessors),
        ("DataWidth", f"{cpu.DataWidth} bits"),
        ("AddressWidth", f"{cpu.AddressWidth} bits"),
        ("SocketDesignation", cpu.SocketDesignation),
        ("VMMonitorModeExtensions", cpu.VMMonitorModeExtensions),
        ("VirtualizationFirmwareEnabled", cpu.VirtualizationFirmwareEnabled),
        ("SecondLevelAddressTranslationExtensions",
         cpu.SecondLevelAddressTranslationExtensions),
    ]
    idx = info.index(("SocketDesignation", cpu.SocketDesignation)) - 1
    for num, cache in enumerate(C.Win32_CacheMemory(), start=1):
        info.insert(idx + num, (f"L{num} Cache", f"{cache.InstalledSize} Kb"))
    return info


def gpus() -> list[list[tuple[str, str | int]]]:
    "Return gpus information."

    info: list[list[tuple[str, str | int]]] = []

    for idx, gpu in enumerate(C.Win32_VideoController()):
        date_str, time_str = gpu.DriverDate.split('.')
        driver_date = datetime.datetime.strptime(date_str, '%Y%m%d%H%M%S')
        driver_date += datetime.timedelta(minutes=int(time_str[-3:]))
        formatted_driver_date = driver_date.strftime('%Y-%m-%d %H:%M:%S')

        gpu_name = gpu.Name
        gpu_caption = gpu.Caption
        gpu_description = gpu.Description

        info.append([
            ("Name", gpu.Name),
            ("DriverVersion", gpu.DriverVersion),
            ("DriverDate", formatted_driver_date),
            ("VideoProcessor", gpu.VideoProcessor),
            ("AdapterRam", f"{(gpu.AdapterRAM or 0) / 10 ** 9} GB"),
            ("MinRefreshRate", f"{gpu.MinRefreshRate} Hz"),
            ("MaxRefreshRate", f"{gpu.MaxRefreshRate} Hz"),
            ("Current RefreshRate", f"{gpu.CurrentRefreshRate} Hz"),
            ("Current Resolution",
             f"{gpu.CurrentHorizontalResolution} x {gpu.CurrentVerticalResolution} pixels"),

            ("CurrentScanMode", gpu.CurrentScanMode),
            ("CurrentBitsPerPixel", gpu.CurrentBitsPerPixel),
            ("CurrentNumberOfColors", gpu.CurrentNumberOfColors),
            ("DeviceID", gpu.DeviceID),
        ])

        if gpu_name != gpu_description:
            info[idx].insert(1, ("Description", gpu_description))
            if gpu_caption not in (gpu_name, gpu_description):
                info[idx].insert(2, ("Caption", gpu_caption))
        elif gpu_name != gpu_caption:
            info[idx].insert(1, ("Caption", gpu_caption))
    return info


def rams() -> list[list[tuple[str, str | int]]]:
    "Return rams information."

    info: list[list[tuple[str, str | int]]] = []

    for memory in C.Win32_PhysicalMemory():
        info.append([
            ("Capacity", f"{int(memory.Capacity or 0) / 10 ** 9} GB"),
            ("Speed", f"{memory.Speed} Mhz"),
            ("ConfiguredClockSpeed", f"{memory.ConfiguredClockSpeed} Mhz"),
            ("ConfiguredVoltage", f"{memory.ConfiguredVoltage} mV"),
            ("VoltageRange", f"{memory.MinVoltage}-{memory.MaxVoltage} mV"),
            ("DataWidth", f"{memory.DataWidth} bits"),
            ("TotalWidth", f"{memory.TotalWidth} bits"),
            ("InterleavePosition", memory.InterleavePosition),
            ("InterleaveDataDepth", memory.InterleaveDataDepth),
            ("SMBIOSMemoryType", memory.SMBIOSMemoryType),
            ("TypeDetail", f"{memory.TypeDetail}"),
            ("FormFactor", memory.FormFactor),
            ("Manufacturer", memory.Manufacturer),
            ("SerialNumber", memory.SerialNumber),
            ("Part Number", memory.PartNumber),
            ("DeviceLocator", memory.DeviceLocator),
        ])
    return info


def disks() -> list[list[tuple[str, str | int]]]:
    "Return disks information."

    info: list[list[tuple[str, str | int]]] = []

    for disk in C.Win32_DiskDrive():
        info.append([
            ("Model", disk.Model),
            ("Size", f"{int(disk.Size or 0) / 10 ** 9} GB"),
            ("FirmwareRevision", disk.FirmwareRevision),
            ("Interface Type", disk.InterfaceType),
            ("TotalHeads", disk.TotalHeads),
            ("TotalCylinders", disk.TotalCylinders),
            ("TotalTracks", disk.TotalTracks),
            ("TracksPerCylinder", disk.TracksPerCylinder),
            ("TotalSectors", disk.TotalSectors),
            ("SectorsPerTrack", disk.SectorsPerTrack),
            ("Serial Number", disk.SerialNumber.strip()),
        ])
    return info


def net_adapters() -> list[list[tuple[str, str | int]]]:
    "Return network adapters information."

    idx: int = 0
    info: list[list[tuple[str, str | int]]] = []

    for adapter in C.Win32_NetworkAdapter():
        if adapter.AdapterTypeID is None:
            continue

        adapter_name = adapter.Name
        product_name = adapter.ProductName
        description = adapter.Description

        info.append([
            ("Name", adapter_name),
            ("Speed", f"{int(adapter.Speed or 0) / 1000000} mbps"),
            ("MAC Address", adapter.MACAddress),
            ("Net Connection ID", adapter.NetConnectionID),
            ("AdapterType", adapter.AdapterType),
            ("Manufacturer", adapter.Manufacturer),
            ("PNPDeviceID", adapter.PNPDeviceID)
        ])

        if adapter_name != product_name:
            info[idx].insert(1, ("ProductName", product_name))
            if description not in (adapter_name, product_name):
                info[idx].insert(2, ("Description", description))
        elif adapter_name != description:
            info[idx].insert(1, ("Description", description))
        idx += 1
    return info


def motherboard() -> list[tuple[str, str]]:
    "Return motherboard information."

    board = C.Win32_BaseBoard()[0]
    return [
        ("Manufacturer", board.Manufacturer),
        ("Product", board.Product),
        ("Serial Number", board.SerialNumber),
        ("Version", board.Version),
    ]


def os_info() -> list[tuple[str, str | int]]:
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

    # ("Total Visible Memory Size", f"{os.TotalVisibleMemorySize} bytes"),
    # ("Free Physical Memory", f"{os.FreePhysicalMemory} bytes"),
    # ("Total Virtual Memory Size", f"{os.TotalVirtualMemorySize} bytes"),
    # ("Free Virtual Memory", f"{os.FreeVirtualMemory} bytes"),
