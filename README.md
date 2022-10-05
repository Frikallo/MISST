[![GitHub release](https://img.shields.io/github/release/frikallo/misst.svg)](https://GitHub.com/frikallo/misst/releases/) ![Github All Releases](https://img.shields.io/github/downloads/frikallo/misst/total?color=blue) ![License](https://img.shields.io/github/license/frikallo/misst?color=blue) ![Hits-of-Code](https://hitsofcode.com/github/frikallo/MISST?branch=main)
# MISST v2.0.2

![](src/assets/showcaseimage1.jpeg)
| _`MISST` on Windows 11 with dark mode and 'Blue' theme with 'Micheal Jackson's Chicago' playing_

![](src/assets/showcaseimage2.jpeg)
| _`MISST` on Windows 11 with dark mode and 'Dark-Blue' theme with 'Jojis's Gimme Love' playing_
###

Original Repository of MISST : **M**usic/**I**nstrumental **S**tem **S**eparation **T**ool.

This application uses state-of-the-art source separation models to extract the 4 core stems from audio files (Bass, Drums, Other Instrumentals and Vocals). But it is not limited to this. MISST acts as a developped music player aswell, fit to enjoy and medal with your audio files as you see fit. MISST even comes prepared to import songs and playlists directly from your music library.

This project is OpenSource, feel free to use, study and/or send pull request.

## Objectives:
- [x] Import songs and playlists from your music library
- [x] Play your songs and playlists
- [x] Extract and manipulate the 4 core stems from your audio files as they play
- [x] Save your stems as audio files
- [x] If imported from your music library, view lyrics and metadata just as you would in your old music player
- [x] Minimal memory usage
- [ ] Make it as fast as possible (Preprocessing, Model loading, etc.)
- [ ] Stable on Windows, Linux and MacOS
- [x] Stable on 32 and 64 bits
- [ ] Proper installer/updater


## Installation
as of version 2.0.2, MISST is not available for any platform with guaranteed compatibility. Until a later version, please refer to [Manual Installation](https://github.com/Frikallo/MISST/#manual-installation-for-developers) .

### Application Notes

- Nvidia GPUs with at least 8GBs of V-RAM are recommended.
- This application is only compatible with 64-bit platforms. 
- This application relies on FFmpeg to process non-wav audio files.
- These models are computationally intensive. Please proceed with caution and pay attention to your PC to ensure it doesn't overheat. ***I am not responsible for any hardware damage.***

### Issue Reporting

Please be as detailed as possible when posting a new issue. 

If possible, check the "log.log" file in your install directory for detailed error information that can be provided to me.

## Manual Installation (For Developers)

These instructions are for those installing MISST v2.0.2 **manually** only.

1. Download & install Python 3.9 or higher (but no lower than 3.9) [here](https://www.python.org/downloads/)
    - **Note:** Ensure the *"Add Python to PATH"* box is checked
2. Download the Source code [here](https://github.com/Frikallo/MISST/archive/refs/tags/v2.0.2.zip)
3. Open the command prompt from the src directory and run the following commands, separately - 

```
pip install -r requirements.txt
```
```
pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111 torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html
```

From here you should be able to open and run the main.py file

- FFmpeg 

    - FFmpeg must be installed and configured for the application to process any track that isn't a *.wav* file. You will need to look up instruction on how to configure it on your operating system.

## License

The **MISST** code is [GPL-licensed](LICENSE). 

- **Please Note:** For all third-party application developers who wish to use our models, please honor the GPL license by providing credit to MISST and its developer.

## Contributing

- For anyone interested in the ongoing development of **MISST**, please send us a pull request, and we will review it. 
- This project is 100% open-source and free for anyone to use and modify as they wish. 
- We only maintain the development and support for the **MISST** and the models provided. 