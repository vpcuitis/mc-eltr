from collections import UserDict
import zipfile
from pathlib import Path
import json
from tabulate import tabulate
import io
from blockLootPair import BlockLootPair

# TODO: write class for pairings
# wrapper around dict for working with loot tables
class LootTables(UserDict):

    #TODO: make the vanilla table a shared class variable
    __original = {}

    def __init__(self):
        self.__staging = {}

    def __setitem__(self, key, value):
        
        pass

    # accepts a path to the .jar and initializes loot tables from the chosen subfolders
    def initFromJar(
        self,
        jarPath: Path,
        subfoldersChosen: dict,
    ):
        lootTablesFolder = "data/minecraft/loot_tables"
        subfolderPaths = tuple(
            list((Path(lootTablesFolder) / sf).as_posix() for sf in subfoldersChosen)
        )

        try:
            jar = zipfile.ZipFile(jarPath)
        except FileNotFoundError:
            print("Could not find the minecraft .jar file " + str(jarPath))
            exit()

        for filePath in jar.namelist():
            if filePath.startswith(subfolderPaths):
                 # short name e.g. "dirt"
                key = Path(filePath).stem
                data = json.load(jar.open(filePath))
                # any metadata we want to add based on the json, we would do so here
                self[key] = BlockLootPair(filePath, data, filePath)
                # keep a record of the original pairing
                self.__original[key] = BlockLootPair(filePath, data, filePath)

        jar.close()

        return self


    # dumps to the console by default for debugging
    def dumpCheatSheet(self, outFile: Path = None):

        columns = {
            "Block": list(Path(fname).stem for fname in self),
            "Loot table": list(Path(self[fname]["srcFile"]).stem for fname in self),
        }

        output = tabulate(columns, headers=["Block", "Loot Table"])

        if outFile is not None:
            f = open(outFile, "w")
            print(output, file=f)
            f.close()
        else:
            print(output)

    def writeToDatapack(self, name, desc, resetMsg, outFile):
        buffer = io.BytesIO()
        datapack = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)

        for filename in self:
            datapack.writestr(filename, json.dumps(self[filename]))

        datapack.writestr(
            "pack.mcmeta",
            json.dumps(
                {"pack": {"pack_format": 1, "description": desc}}, indent=4
            ),
        )

        datapack.writestr(
            "data/minecraft/tags/functions/load.json",
            json.dumps({"values": [name + ":reset"]}),
        )

        datapack.writestr(
            "data/" + name + "/functions/reset.mcfunction",
            resetMsg,
        )

        datapack.close()

        fileOnDisk = open(outFile, "wb")
        fileOnDisk.write(buffer.getvalue())
        fileOnDisk.close()
