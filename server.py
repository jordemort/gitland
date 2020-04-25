#!/usr/bin/env python3

import os, requests, time

class GameServer:
    def log(self, text):
        open("log", "a").write(text + "\n")
        print(text)

    def main(self):
        while True:
            self.log("next turn")
            self.addPlayers()
            self.updateGameState()
            self.log("turn done")
            os.system("git add -A")
            os.system("git commit -m \"next turn\"")
            os.system("git push origin master")
            time.sleep(15)

    def addPlayers(self):
        # players request to join via issue
        joinRequests = requests.get(
            "https://api.github.com/repos/programical/gitland/issues?state=open",
            headers={"Accept":"application/vnd.github.v3+json"}
        ).json()

        for request in joinRequests:
            newPlayer = request["user"]["login"]
            team = request["title"]

            # make sure they chose an existing team
            if team not in ("cg", "cr", "cb"):
                self.log(newPlayer + " didn't join - invalid team name")
                return

            # make sure they aren't already playing
            for player in os.listdir("players"):
                if player == newPlayer:
                    self.log(newPlayer + " didn't join - already playing")
                    return

            self.spawnPlayer(newPlayer, team)

    def addPlayerData(self, player: str, team: str, x: int, y: int):
        os.makedirs("players/" + player)
        open("players/" + player + "/team", "w").write(team)
        open("players/" + player + "/x", "w").write(str(x))
        open("players/" + player + "/y", "w").write(str(y))

    def spawnPlayer(self, player: str, team: str):
        # spawn in friendly territory
        x, y = 0, 0
        for row in open("map").read().split("\n"):
            x = 0
            for tile in row.split(","):
                teamTile = team.replace("c", "u") # lazy hack
                if tile == teamTile:
                    self.addPlayerData(player, team, x, y)
                    self.log(player + " joined " + team + " on " + teamTile + str(x) + "/" + str(y))
                    return

                x += 1
            y += 1

        # if that fails, try no man's land
        x, y = 0, 0
        for row in open("map").read().split("\n"):
            x = 0
            for tile in row.split(","):
                if tile == "ux":
                    self.addPlayerData(player, team, x, y)
                    self.log(player + " joined " + team + " on ux " + str(x) + "/" + str(y))
                    return

                x += 1
            y += 1

        # failed. print the team too, for debug purposes
        self.log(player + " didn't join " + team + " - no free space")

    def loadMap(self) -> list:
        world = []
        for row in open("map").read().split("\n"):
            world.append(row.split(","))

        return world

    def saveMap(self, world: list):
        open("map", "w").write(self.mapToStr(world))

    def drawMap(self, world: list):
        # in no way can this ever backfire
        mapStr = self.mapToStr(world).replace("ux", "![](icons/ux)").replace("ug", "![](icons/ug)").replace("ur", "![](icons/ur)").replace("ub", "![](icons/ub)").replace("cg", "![](icons/cg)").replace("cr", "![](icons/cr)").replace("cb", "![](icons/cb)").replace(",", " ").replace("\n", "  \n")
        open("README.md", "w").write(mapStr)

    def mapToStr(self, world: list) -> str:
        mapString = ""
        for row in world:
            mapString += ",".join(row) + "\n"
        return mapString

    def movePlayer(self, playerToMove: str, x: int, y: int):
        if x < 0 or y < 0 or x > 22 or y > 22:
            self.log(playerToMove + " tried to walk out of the map")
            return

        for player in os.listdir("players"):
            if os.path.isdir("players/" + player) and player != playerToMove:
                occupiedX = int(open("players/" + player + "/x").read().strip())
                occupiedY = int(open("players/" + player + "/y").read().strip())
                if x == occupiedX and y == occupiedY:
                    self.log(playerToMove + " bumped into " + player)
                    return

        open("players/" + playerToMove + "/x", "w").write(str(x))
        open("players/" + playerToMove + "/y", "w").write(str(y))
        self.log(playerToMove + " moved to " + str(x) + "/" + str(y))

    def updateGameState(self):
        world = self.loadMap()

        # don't carry over player position data, only control
        x, y = 0, 0
        for row in world:
            x = 0
            for tile in row:
                world[y][x] = tile.replace("cg", "ug").replace("cb", "ub").replace("cr", "ur")
                x += 1
            y += 1

        # add players
        for player in os.listdir("players"):
            if os.path.isdir("players/" + player):
                x = int(open("players/" + player + "/x").read().strip())
                y = int(open("players/" + player + "/y").read().strip())

                # player input
                action = requests.get(
                    "https://raw.githubusercontent.com/" + player + "/gitland-client/master/act"
                ).text.strip()

                if action == "left":
                    self.movePlayer(player, x - 1, y)
                elif action == "right":
                    self.movePlayer(player, x + 1, y)
                elif action == "up":
                    self.movePlayer(player, x, y - 1)
                elif action == "down":
                    self.movePlayer(player, x, y + 1)
                else:
                    self.log(player + " didn't do anything")

                # reload after player moves
                icon = open("players/" + player + "/team").read().strip()
                x = int(open("players/" + player + "/x").read().strip())
                y = int(open("players/" + player + "/y").read().strip())

                world[y][x] = icon

        self.saveMap(world)
        self.drawMap(world)

def main():
    server = GameServer()
    server.main()

if __name__ == "__main__":
    main()
