import pyglet
from math import *
from pyglet.graphics.shader import ShaderProgram
from pyglet.math import *

# All objects parent class, also pyglet graphics group
class Object(pyglet.graphics.Group):
    def __init__(self):
        super().__init__()
        self.delta = 0
        
    # Scene setups this object
    def setup(self, program: ShaderProgram, batch: pyglet.graphics.Batch):
        self.program = program
        self.vbo(program, batch)

    def vbo(self, program: ShaderProgram, batch: pyglet.graphics.Batch):
        ...

    def tick(self, delta: float):
        self.delta += delta

    def update(self):
        self.delta = 0
    
    def set_state(self):
        self.program.use()

    def unset_state(self):
        self.program.stop()

    def __hash__(self):
        return hash(self.parent)

class Cube(Object):
    def __init__(self, position=Vec3(), scale=Vec3(1.0, 1.0, 1.0)):
        super().__init__()
        self.position = position
        self.rotation = Vec3()
        self.scale = scale
        self.value = 0.0

    def update(self):
        distance = self.position.length()
        
        self.value += self.delta
        self.position = Vec3(
            cos(self.value)*distance,
            self.position.y,
            sin(self.value)*distance
        )

        self.rotation += Vec3(0.0, self.delta-distance/4000, 0.0)

        self.delta = 0

    def set_state(self):
        self.program.use()
        self.update()

        translation = Mat4.from_translation(self.position)
        scale = Mat4.from_scale(self.scale)
        
        rotation_pitch = Mat4.from_rotation(self.rotation.x, Vec3(1.0, 0.0, 0.0))
        rotation_yaw = Mat4.from_rotation(self.rotation.y, Vec3(0.0, 1.0, 0.0))
        rotation_roll = Mat4.from_rotation(self.rotation.z, Vec3(0.0, 0.0, 1.0))
        rotation = rotation_pitch @ rotation_yaw @ rotation_roll

        self.program['model'] = translation @ rotation @ scale

    def vbo(self, program, batch):
        self.list = program.vertex_list_indexed(
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
            colors=('Bn', [255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 0, 255]*2)
        )

    def __eq__(self, other):
        return (self.position == other.position, self.rotation == other.rotation, self.scale == other.scale)

    def __hash__(self):
        return hash((self.position, self.rotation, self.scale))