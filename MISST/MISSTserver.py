import requests
import shutil
import os 

class MISSTserver():
    def __init__(self, serverBase):
        self.serverBase = serverBase
        self.demucsPost = f"{self.serverBase}/demucs-upload"
        self.demucsGet = f"{self.serverBase}/download"
        self.demucsQueue = f"{self.serverBase}/queue"
        self.demucsCoverArt = f"{self.serverBase}/getcoverart"
        self.demucsPostCoverArt = f"{self.serverBase}/postcoverart"

    def prepDemucs(self, file):
        # Preprocess the file with Demucs on remote server
        # Path: MISST\MISSTserver.py
        # file: The file to be prepared
        req = requests.post(self.demucsPost, files={"file": open(file, "rb")})
        return f"File Successfully Preprocessed ({req.content}))"
    
    def getDemucs(self, id, saveDest, saveName):
        # Get the processed file from the remote server
        # Path: MISST\MISSTserver.py
        # id: The id of the file to be retrieved
        req = requests.get(f"{self.demucsGet}/{id}.zip")
        name = id.replace('_', ' ')
        open(f"{name}.zip", "wb").write(req.content)
        shutil.unpack_archive(f"{name}.zip", f"{saveDest}/{saveName}")
        os.remove(f"{name}.zip")
        return f"{id}.zip"
    
    def startDemucsQueue(self):
        # Start the Demucs queue on the remote server
        # Path: MISST\MISSTserver.py
        req = requests.post(self.demucsQueue)
        return f"Out of Queue ({req.content}))"
    
    def getDemucsCoverArt(self, name):
        # Get the cover art from the remote server
        # Path: MISST\MISSTserver.py
        # id: The id of the file to be retrieved
        req = requests.get(f"{self.demucsCoverArt}/{name}.png")
        return req.content
    
    def postDemucsCoverArt(self, file):
        # Post the cover art to the remote server
        # Path: MISST\MISSTserver.py
        # id: The id of the file to be retrieved
        # file: The file to be uploaded
        req = requests.post(self.demucsPostCoverArt, files={"file": open(file, "rb")})
        return f"Cover Art Successfully Uploaded ({req.content}))"
    
    def getAverageWaitTime(self):
        # Get the average wait time of the queue
        # Path: MISST\MISSTserver.py
        try:
            req = requests.get(f"{self.serverBase}/getaverage", timeout=1)
        except:
            return "N/A"
        
        try:
            return int(req.content)
        except:
            return "N/A"
    

if __name__ == "__main__":
    server = MISSTserver("http://66.175.221.76:5001")
    print(server.startDemucsQueue())
    print(server.prepDemucs("C:\\Users\\noahs\\Desktop\\Repos\\MISSTcodebase\\Barenaked Ladies - Brian Wilson.mp3"))
    print(server.getDemucs("test"))
    print(server.postDemucsCoverArt("test.png"))
    print(server.getDemucsCoverArt("test"))