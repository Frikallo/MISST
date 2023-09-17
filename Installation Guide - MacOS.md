# How to get started with MISST - MacOS

## **Manual installation on Mac0S using miniconda3**

This worked for @[CAprogs](https://github.com/CAprogs) on a **MacbookPro 2021 M1 pro**. 
#
## _**Follow these steps**_
if you don't have **MINICONDA** , you should install it using this [**link**](https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.pkg).

#
For **Pyaudio** package you should install [**Homebrew**](https://github.com/Homebrew/brew/releases/latest) first.

Then run `brew install portaudio` in your **terminal** ( this is required to install **pyaudio** later )
#
Now follow these steps 🤓
- Download the **MISST Zip file** [**here**](https://github.com/Frikallo/MISST/archive/refs/tags/V3.1.0.zip)
- Create your virtual env using **conda** _(Copy and paste in your Terminal)_

Enter `miniconda3` folder ⬇️
```
cd miniconda3
```
#
Create a `venv` named _**MISSTvenv**_ ⬇️
```
conda create --name MISSTvenv
```
#
Activate the  `MISSTvenv` ⬇️
```
conda activate MISSTvenv
```
#
Install `pip` ( inside the MISSTvenv ) ⬇️
```
conda install pip
```
#
Install _**the requirements packages**_ ( inside the MISSTvenv ). 

Replace < `path/to/requirements.txt` > with your **path** to the **requirements.txt** file ⬇️
```
conda install --file path/to/requirements.txt
```
#
At this point I encountered some `issues` when installing **packages** with `pip` / `conda`. ( All packages weren't installed )
#
Before proceeding, please ensure that you have `Git` **installed** on your macOS system.
- In your terminal, enter the following command ⬇️
```
git --version
```
1. If you see the **Git version** displayed, it means `Git` is **already installed** on your system, and you can proceed to the next step.

2. If `Git` is **not installed**, you can install it using `Homebrew` ⬇️ ( See the Doumentation [**here**](https://git-scm.com/download/mac) )
```
brew install git
```
#
Now just run the following command ( inside the MISSTvenv ) ⬇️
```
pip install -r requirements.txt                                 ( GPU )
pip install -r requirements-minimal.txt                         ( CPU )
```
If that doesn't work, try installing the packages one by one ⬇️
```
pip install customtkinter git+https://github.com/Frikallo/gputil.git@master music_tag psutil PILLOW pypresence lyrics_extractor demucs pyaudio soundfile scipy vcolorpicker
```
Then install torch with or without `CUDA` ⬇️
```
pip install torch==2.0.1+cu117 torchaudio==2.0.2+cu117 torchvision==0.15.2+cu117 -f https://download.pytorch.org/whl/torch_stable.html
```
```
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
```

Then **run** ( inside the MISSTvenv ) ⬇️
```
conda install pyqt
```
#
- Enter the `MISSTapp.py` Folder ( replace with the real path )
```
 cd path/to/MISSTapp.py
```
- `Run` the App 🧞‍♂️  ( inside the MISSTvenv )

```
 python MISSTapp.py
```

