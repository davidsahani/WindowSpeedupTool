## WindowSpeedupTool Build Instructions

To successfully build WindowSpeedupTool, please follow these instructions:

### Prerequisites

1. Ensure that you have a C++ compiler installed on your system.

   > **On Windows:**
   > 
   > If you have Visual Studio 2019 or a later version installed, make sure to check the following prerequisites:
   > - Verify that the Windows 10 SDK (10.0.18362 or later) is installed. If not, install it.
   > - Use Visual Studio's installer to install the "C++ for MFC for ..." package.
   >
   > Alternatively, you can install the Visual Studio Build Tools from the following link:
   > https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Building WindowSpeedupTool

1. Open a command prompt or terminal and navigate to the project root directory of the WindowSpeedupTool.

2. Install the required dependencies by running the following command:
   ```
   pip install -r requirements.txt
   ```

3. Install pyinstaller by executing the following command:
   ```
   pip install pyinstaller
   ```

4. To build WindowSpeedupTool, execute the following command:
   ```
   python build.py
   ```

This command will compile the project and create a directory containing application files along with its executable. Which directory will be available in the `project/build` directory.

### Creating Setup Installer

1. Download Inno Setup from here: https://jrsoftware.org/isinfo.php

2. Open the `setup.iss` file with Inno Setup.

3. First, build the project and then compile it using Inno Setup.

After the compilation process is complete, the installer executable will be created and placed in the `project/build` directory.