import pyglet
from math import *
from pyglet.graphics.shader import ShaderProgram
from pyglet.math import *

# Override objects classes
class Object: ...
class RenderObject: ...
class Color: ...

class Color:
    def __init__(self, r: int, g: int, b: int, alpha: int):
        self.r, self.g, self.b, self.alpha = r, g, b, alpha

    def array(self, count: int) -> list:
        return [self.r, self.g, self.b, self.alpha]*count

# Main render type (aka object model), contains refference to scene object
# Parent class for Default objects (just model matrix) render object
class RenderObject(pyglet.graphics.ShaderGroup):
    def __init__(self):
        self.position = Vec3()
        self.rotation = Vec3()
        self.color = Color(255, 255, 255, 255)
        self.scale = Vec3(1.0, 1.0, 1.0)

    # Link RenderObject and RenderObject
    def setup(self, program: ShaderProgram, batch: pyglet.graphics.Batch, parent_object: Object):
        self.program = program
        super().__init__(self.program)

        # Link parent object and render object
        self.parent_object = parent_object
        self.move_data()
        self.vbo(batch)
        
    # Update state function
    def update_state(self):
        translation = Mat4.from_translation(self.position)
        scale = Mat4.from_scale(self.scale)
        
        rotation_pitch = Mat4.from_rotation(self.rotation.x, Vec3(1.0, 0.0, 0.0))
        rotation_yaw = Mat4.from_rotation(self.rotation.y, Vec3(0.0, 1.0, 0.0))
        rotation_roll = Mat4.from_rotation(self.rotation.z, Vec3(0.0, 0.0, 1.0))
        rotation = rotation_pitch @ rotation_yaw @ rotation_roll

        self.program['model'] = translation @ rotation @ scale

    # draw state
    def set_state(self):
        self.program.use()
        self.move_data()
        self.update_state()

    def unset_state(self):
        self.program.stop()

    # Calls before drawing frame, moves object data to render object
    def move_data(self):
        for (arg, data) in self.parent_object.__dict__.items():
            self.__dict__[arg] = data
    
    def vbo(self, batch: pyglet.graphics.Batch):
        ...

    def __hash__(self):
        return hash((self.position, self.rotation, self.scale))

class Cube(RenderObject):
    def vbo(self, batch):
        self.program.vertex_list_indexed(
            count=8,
            mode=pyglet.gl.GL_TRIANGLES,
            indices = (
                2, 6, 7, 2, 3, 7,
                0, 4, 5, 0, 1, 5,
                0, 2, 6, 0, 4, 6,
                1, 3, 7, 1, 5, 7,
                0, 2, 3, 0, 1, 3,
                4, 6, 7, 4, 5, 7
            ),
            batch=batch,
            group=self,
            vertices=('f', (
                -10.0, -10.0, 10.0, 10.0, -10.0, 10.0, # 0 1
                -10.0, 10.0, 10.0, 10.0, 10.0, 10.0, # 2 3
                -10.0, -10.0, -10.0, 10.0, -10.0, -10.0, # 4 5
                -10.0, 10.0, -10.0, 10.0, 10.0, -10.0 # 6 7
            )),
            colors=('Bn', self.color.array(8))
        )

    def __hash__(self):
        return hash((self.position, self.rotation, self.scale))

# Scene object, linked with RenderObject
class Object:
    def __init__(self, **kwargs):
        self.position = Vec3()
        self.rotation = Vec3()
        self.scale = Vec3(1.0, 1.0, 1.0)

        for (arg, data) in kwargs.items():
            self.__dict__[arg] = data

    def update(self, delta: float):
        distance = self.position.length()
        
        self.value += delta*self.speed
        self.position = Vec3(
            cos(self.value)*distance,
            self.position.y,
            sin(self.value)*distance
        )
        self.rotation += Vec3(0.0, delta-distance/4000, 0.0)