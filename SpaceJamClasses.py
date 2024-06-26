"""
Highest level classes for SpaceJam.
"""

import re
#import math

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.interval.LerpInterval import LerpFunc
from direct.particles.ParticleEffect import ParticleEffect
from typing import Callable

from CollideObjectBase import *
from panda3d.core import *


class Universe(InverseSphereCollideObj):
    def __init__(self,
                 loader: Loader, parentNode: NodePath,
                 nodeName: str, modelPath: str,   
                 texPath: str, 
                 posVec: Vec3, hpr: Vec3, scaleVec: float):

        super(Universe, self).__init__(loader, parentNode, nodeName, modelPath, Vec3(0,0,0), 0.9)

        self.modelNode.setTexture(loader.loadTexture(texPath), 1)
        
        self.modelNode.setPos(posVec)
        self.modelNode.setHpr(hpr) 
        self.modelNode.setScale(scaleVec)    

class Planet(SphereCollideObj):
    def __init__(self,
                 loader: Loader, parentNode: NodePath,
                 nodeName: str, modelPath: str,   
                 texPath: str, 
                 posVec: Vec3, hpr: Vec3, scaleVec: float):

        super(Planet, self).__init__(loader, parentNode, nodeName, modelPath, Vec3(0,0,0), 1.1)
        
        self.modelNode.setTexture(loader.loadTexture(texPath), 1)
        
        self.modelNode.setPos(posVec)
        self.modelNode.setHpr(hpr) 
        self.modelNode.setScale(scaleVec)       

class SpaceStation(CapsuleCollidableObject): 
    def __init__(self,
                 loader: Loader, parentNode: NodePath,
                 nodeName: str, modelPath: str,   
                 texPath: str, 
                 posVec: Vec3, hpr: Vec3, scaleVec: float):

        super(SpaceStation, self).__init__(loader, parentNode, nodeName, modelPath, 5, 0, 5, -7.5, 0, -10, 10)
        
        self.modelNode.setTexture(loader.loadTexture(texPath), 1)
        
        self.modelNode.setPos(posVec)
        self.modelNode.setHpr(hpr) 
        self.modelNode.setScale(scaleVec)      

class Drone(CapsuleCollidableObject):
    
    droneCount = 0
    
    def __init__(self,
                 loader: Loader, parentNode: NodePath,
                 nodeName: str, modelPath: str,   
                 texPath: str, 
                 posVec: Vec3, hpr: Vec3, scaleVec: float):

        super(Drone, self).__init__(loader, parentNode, nodeName, modelPath, 0, 0.5, 0.5, 0, -0.5, -0.5, 3) 
        self.modelNode.setTexture(loader.loadTexture(texPath), 1)
        
        self.modelNode.setPos(posVec)
        self.modelNode.setHpr(hpr) 
        self.modelNode.setScale(scaleVec)       

class Player(CapsuleCollidableObject):
    def __init__(self,
                 loader: Loader, parentNode: NodePath,
                 nodeName: str, modelPath: str,   
                 texPath: str, 
                 posVec: Vec3, hpr: Vec3, scaleVec: float,
                 taskMgr: Task, renderer: NodePath, accept: Callable[[str, Callable], None], 
                 traverser: CollisionTraverser):

        super(Player, self).__init__(loader, parentNode, nodeName, modelPath, 0, 0, 5, 0, 0, 4, 15) 
        
        self.modelNode.setTexture(loader.loadTexture(texPath), 1)
        
        self.modelNode.setPos(posVec)
        self.modelNode.setHpr(hpr) 
        self.modelNode.setScale(scaleVec)  
        
        self.taskManager = taskMgr
        self.render = renderer
        self.loader = loader
        self.accept = accept
        
        self.traverser = traverser
        self.handler = CollisionHandlerEvent()
        
        self.reloadTime = 0.25
        self.missileDistance = 4000
        self.missileBay = 1 #Num missiles that can be launched at one time
        self.taskManager.add(self.checkIntervals, "checkMissiles", 34)
        
        self.explosionCount = 0 #num explosion particles
        self.explodeIntervals = {}
        
        #ads logic to detect missile collisions
        self.handler.addInPattern("into")
        self.accept("into", self.handleInto)
        
        self.turnRate = 0.5
        self.setKeybinds()
        self.setParicles()
        
    def handleInto(self, entry):
        pattern = r"[0-9]" #used to remove numberic charachters from string
        
        fromNode = entry.getFromNodePath().getName()
        intoNode = entry.getIntoNodePath().getName()
        intoPosition = Vec3(entry.getSurfacePoint(self.render))
        
        tempVar = fromNode.split("_")
        shooter = tempVar[0]
        
        tempVar = intoNode.split("-")
        tempVar = intoNode.split("_")
        victim = tempVar[0]
        strippedStr = re.sub(pattern, "", victim)

        print(f"fromNode: {fromNode}")
        print(f"intoNode: {intoNode}")
        
        if (strippedStr == "Drone"):
            print(f"{shooter} is DONE.")
            print(f"{victim} hit at {intoPosition}")
            self.droneDestroy(victim, intoPosition)
        Missile.intervals[shooter].finish()
        
    def droneDestroy(self, hitId, hitPosition):
        nodeID = self.render.find(hitId)
        nodeID.detachNode()
        
        self.explodeNode.setPos(hitPosition)
        self.explode(hitPosition)
        
    def explode(self, impactPoint):
        self.explosionCount += 1
        tag = f"particles-{str(self.explosionCount)}"
        
        self.explodeIntervals[tag] = LerpFunc(self.explodeLight, fromData=0, toData=1, duration=2.0, extraArgs=[impactPoint])
        #shorted above animation so no secondary explosion occurs 
        #Above Builds animation for explosion
        self.explodeIntervals[tag].start()
    
    def explodeLight(self, time, explodePosition):
        if (time == 1.0 and self.explodeEffect): #If 1 second has passed, and there is an explosion taking place
            self.explodeEffect.disable()
        elif time == 0:
            self.explodeEffect.start(self.explodeNode)
            
    def setParicles(self):
        base.enableParticles()
        self.explodeEffect = ParticleEffect()
        self.explodeEffect.loadConfig("./Assets/Part-Efx/basic_xpld_efx.ptf")
        self.explodeEffect.setScale(20)
        self.explodeNode = self.render.attachNewNode("ExplosionEffects")
        
    def fire(self):
        if self.missileBay:
            travelRate = self.missileDistance #might be able to remove
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward()) #can condense with trajectory from ship call
            aim.normalize()
            fireSolution = aim * travelRate
            inFront = aim * 150 
            """
            FIXME:
            With current implementation, the missles will not blow up drones right next to the ship, 
            as the missile will spawn past these drones. Can resize all drones to be larger than missle, or can make missile larger.
            In either case, a problem for cleanup during final build.
            """
            travelVec = fireSolution + self.modelNode.getPos() #FIXME: COuld getPos() fix my relative movement issues?
            
            self.missileBay -= 1
            tag = "missile " + str(Missile.missileCount)
                
            posVec = self.modelNode.getPos() + inFront #spawns missile in front of the spaceship
            
            CurrentMissile = Missile(self.loader, self.render, tag, "./Assets/Phaser/phaser.egg", posVec, 4.0)
            self.traverser.addCollider(CurrentMissile.collisionNode, self.handler)
            
            Missile.intervals[tag] = CurrentMissile.modelNode.posInterval(2.0, travelVec, startPos = posVec, fluid = 1) #fluid = 1 checks for collisions b/t frames
            Missile.intervals[tag].start()
            
            
        else:
            if not self.taskManager.hasTaskNamed("reload"):
                print("init reload..." )
                self.taskManager.doMethodLater(0, self.reload, 'reload')   
                return Task.cont
            
    def reload(self, task):
        if task.time > self.reloadTime:
            self.missileBay += 1
            print("Reload complete")
            
            if self.missileBay > 1:
                self.missileBay = 1
            
            return Task.done
        
        elif task.time <= self.reloadTime:
            print("reload processing....")
            return Task.cont
            
    def checkIntervals(self, task):
        for i in Missile.intervals:
            if not Missile.intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()
                del Missile.intervals[i]
                del Missile.fireModels[i]
                del Missile.cNodes[i]
                del Missile.collisionSolids[i]
                print(i + " Has reached end of fire solution.")
                break
        return Task.cont

    def setKeybinds(self): 
        self.accept("space", self.thrust, [1])
        self.accept("space-up", self.thrust, [0])
        
        self.accept("f", self.fire)
        
        self.accept("a", self.leftTurn, [1])
        self.accept("a-up", self.leftTurn, [0])
        
        self.accept("d", self.rightTurn, [1])
        self.accept("d-up", self.rightTurn, [0])
        
        self.accept("w", self.upTurn, [1])
        self.accept("w-up", self.upTurn, [0])

        self.accept("s", self.downTurn, [1])
        self.accept("s-up", self.downTurn, [0])
        
        self.accept("arrow_left", self.leftRoll, [1])
        self.accept("arrow_left-up", self.leftRoll, [0])

        self.accept("arrow_right", self.rightRoll, [1])
        self.accept("arrow_right-up", self.rightRoll, [0])
             
    def thrust(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyThrust, "forward-thrust")
        else:
            self.taskManager.remove("forward-thrust")
                      
    def leftTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyLeftTurn, "left-turn")
        else:
            self.taskManager.remove("left-turn")
            #print(self.modelNode.getHpr())
    
    def rightTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyRightTurn, "right-turn")
        else:
            self.taskManager.remove("right-turn")
            #print(self.modelNode.getHpr())    

    def upTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyUpTurn, "up-turn")
        else:
            self.taskManager.remove("up-turn")
            #print(self.modelNode.getHpr())
    
    def downTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyDownTurn, "down-turn")
        else:
            self.taskManager.remove("down-turn")
            #print(self.modelNode.getHpr())
            
    def leftRoll(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyLeftRoll, "left-roll")
        else:
            self.taskManager.remove("left-roll")
            #print(self.modelNode.getHpr())                   

    def rightRoll(self, keyDown):
        if keyDown:
            self.taskManager.add(self.applyRightRoll, "right-roll")
        else:
            self.taskManager.remove("right-roll")
            #print(self.modelNode.getHpr())    
                
    def applyThrust(self, task):
        shipSpeed = 5 #rate of movement
        trajectory = self.render.getRelativeVector(self.modelNode, Vec3.forward()) #Pulls direction ship is facing
        """
        FIXME: If trajectory is set to self.modelNode, then the ship will fly forward regardless of the direction the camera is facing.
        unknown cause, passing in a seperate renderer like is implemented now seems to fix the issue.
        """
        trajectory.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + trajectory * shipSpeed) #controls movement itself
        return Task.cont
    
    #FIXME: Old methods for relative direction error at odd angles. Scraped for now, might try to reimplement later. 
    """
    def applyLeftTurn(self, task):
        rotation = self.modelNode.getHpr()
        vector = self.pullVectorLR(rotation)
        vectorX = vector[0]
        vectorY = vector[1]
        self.modelNode.setHpr(self.modelNode.getH() + vectorX, self.modelNode.getP() + vectorY, self.modelNode.getR())
        return Task.cont    
    
    def applyRightTurn(self, task):
        rotation = self.modelNode.getHpr()
        vector = self.pullVectorLR(rotation)
        vectorX = vector[0]
        vectorY = vector[1]
        self.modelNode.setHpr(self.modelNode.getH() - vectorX, self.modelNode.getP() - vectorY, self.modelNode.getR())
        return Task.cont    

    def applyUpTurn(self, task):
        rotation = self.modelNode.getHpr()
        vector = self.pullVectorUD(rotation)
        vectorX = vector[0] 
        vectorY = vector[1] 
        self.modelNode.setHpr(self.modelNode.getH() + vectorX, self.modelNode.getP() + vectorY, self.modelNode.getR())
        return Task.cont   

    def applyDownTurn(self, task):
        rotation = self.modelNode.getHpr()
        vector = self.pullVectorUD(rotation)
        vectorX = vector[0] 
        vectorY = vector[1] 
        self.modelNode.setHpr(self.modelNode.getH() - vectorX, self.modelNode.getP() - vectorY, self.modelNode.getR())
        return Task.cont   

    #FIXME: Need logic to determine if ship is up or down relative to world (180 <= x < 270 is cutoff for directions reversed, inclusive)
    def pullVectorLR(self, hpr: Vec3):
        
        Pulls XZ vectors to increase in movement direction for left, right movement, and returns as a list in format [x,y]. 
        Needed to fix movement issues where tilting "left" tilts ship left relative to world, not the ship itself
        
        rotation = hpr[2]
        relativeX = self.turnRate * math.cos(math.radians(rotation))
        relativeY = self.turnRate * math.sin(math.radians(rotation))
        cordinateList = [relativeX, relativeY]
        
        return cordinateList
    
    def pullVectorUD(self, hpr: Vec3):
        
        Pulls XZ vector to increase in movement direction for Up, Down movement, abd returns as a list in format [x,z]. 
        Needed to fix movement issues where tilting "up" tilts ship up relative to world, not the ship itself.
        
        rotation = hpr[2] + 90
        relativeX = self.turnRate * math.cos(math.radians(rotation))
        relativeY = self.turnRate * math.sin(math.radians(rotation))
        cordinateList = [relativeX, relativeY]
        
        return cordinateList
    """

    #OLD METHODS FOR TURNING
    def applyLeftTurn(self, task):
        self.modelNode.setH(self.modelNode.getH() + self.turnRate)
        return Task.cont
    
    def applyRightTurn(self, task):
        self.modelNode.setH(self.modelNode.getH() + -self.turnRate)
        return Task.cont
    
    def applyUpTurn(self, task):
        self.modelNode.setP(self.modelNode.getP() + self.turnRate)
        return Task.cont
  
    def applyDownTurn(self, task):
        self.modelNode.setP(self.modelNode.getP() + -self.turnRate)
        return Task.cont
    
    def applyLeftRoll(self, task): 
        self.modelNode.setR(self.modelNode.getR() + -self.turnRate)
        return Task.cont

    def applyRightRoll(self, task): 
        self.modelNode.setR(self.modelNode.getR() + self.turnRate)
        return Task.cont      
    
class Missile(SphereCollideObj):
    fireModels = {}
    cNodes = {}
    collisionSolids = {}
    intervals = {}
    
    missileCount = 0
    
    def __init__(self, loader: Loader, parentNode: NodePath, nodeName: str, modelPath: str, posVec: Vec3, scaleVec: float = 1.0):
        super(Missile, self).__init__(loader, parentNode, nodeName, modelPath, Vec3(0,0,0), 3.0)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setPos(posVec)
        
        Missile.missileCount += 1
        
        Missile.fireModels[nodeName] = self.modelNode
        Missile.cNodes[nodeName] = self.collisionNode
        
        Missile.collisionSolids[nodeName] = self.collisionNode.node().getSolid(0)
        Missile.cNodes[nodeName].show()
        print("Fired torpedo #" + str(Missile.missileCount))