import pyglet

from math import *
from pyglet.math import Vec2, Vec3, Mat4, clamp
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.graphics.vertexdomain import IndexedVertexList

# Target window fps
TARGET_FPS = 240
# Y-axis flipped view-matrix
FLIP = Mat4(
    a=1, b=0, c=0, d=0,
    e=0, f=-1, g=0, h=0,
    i=0, j=0, k=1, l=0,
    m=0, n=0, o=0, p=1,
)

class Camera():
    def __init__(self):
        self.position = Vec3(20.0, 20.0, -20.0)

        self.speed = 40.0
        self.scroll_speed = self.speed*2
        self.sensitivity = 0.2
        self.yaw = pi/4
        self.pitch = -radians(40)
        self.fov = 70.0

        self.motion = Vec2()
        self.scroll = 0.0

        self.buttons = {
            # W
            119: False,
            # A
            97: False,
            # S
            115: False,
            # D
            100: False,
            # F
            102: False,
            # Space
            32: False,
            # LShift
            65505: False,
            # LCtrl
            65507: False
        }

    # forward rotation vector
    def forward(self) -> Vec3:
        return Vec3(cos(self.pitch) * sin(-self.yaw), sin(self.pitch), cos(self.pitch) * cos(-self.yaw))

    def right(self) -> Vec3:
        return Vec3(cos(-self.yaw), 0.0, -sin(-self.yaw))

    def update(self, delta: float):
        speed = self.speed
        # If ctrl - double speed
        if self.buttons[65507]:
            speed *= 2

        # Wasd-movement
        if self.buttons[119]:
            forw = self.forward()
            self.position += forw * speed * delta
        if self.buttons[97]:
            right = self.right()
            self.position += right * speed * delta
        if self.buttons[115]:
            forw = self.forward()
            self.position -= forw * speed * delta
        if self.buttons[100]:
            right = self.right()
            self.position -= right * speed * delta
        
        # Down-Up-movement
        if self.buttons[32]:
            self.position += Vec3(0.0, 1.0, 0.0) * speed * delta
        if self.buttons[65505]:
            self.position += Vec3(0.0, -1.0, 0.0) * speed * delta

        # If F-scroll
        if self.buttons[102]:
            self.fov -= self.scroll
            self.fov = round(clamp(self.fov, 30.0, 145.0))
        elif self.scroll:
            forw = self.forward()
            self.position +=  forw * self.scroll_speed * self.scroll
        
        # Rotate camera
        self.yaw += radians(self.motion.x) * self.sensitivity
        self.pitch += radians(self.motion.y) * self.sensitivity
        self.pitch = clamp(self.pitch, -pi/2, pi/2)

        self.motion = Vec2()
        self.scroll = 0.0

    def on_pressed(self, symbol: int):
        if symbol in self.buttons:
            self.buttons[symbol] = True
    
    def on_released(self, symbol: int):
        if symbol in self.buttons:
            self.buttons[symbol] = False
    
    def on_motion(self, dx, dy):
        self.motion += Vec2(dx, dy)

    def on_scroll(self, dy):
        self.scroll += dy

    # Flipped view matrix
    def view(self) -> Mat4:
        return FLIP @ Mat4.from_translation(self.position)
    
    # Camera projection matrix
    def projection(self, width: int, height: int) -> Mat4:
        return Mat4.perspective_projection(
            width/height, z_near=0.1, z_far=1000, fov=self.fov
        ).rotate(-self.pitch, Vec3(1.0, 0.0, 0.0)).rotate(self.yaw, Vec3(0.0, 1.0, 0.0))

def cube(program: ShaderProgram, batch, pos: Vec3) -> IndexedVertexList:
    vertices = [
        -10.0, -10.0, 10.0, 10.0, -10.0, 10.0, # 0 1
        -10.0, 10.0, 10.0, 10.0, 10.0, 10.0, # 2 3
        -10.0, -10.0, -10.0, 10.0, -10.0, -10.0, # 4 5
        -10.0, 10.0, -10.0, 10.0, 10.0, -10.0 # 6 7
    ]

    p = list(pos)
    for i in range(3):
        for j in range(i, len(vertices), 3):
            vertices[j] += p[i]

    return program.vertex_list_indexed(
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
        vertices=('f', vertices),
        normals=('f', (
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        )),
        colors=('Bn', [255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 0, 255]*2)
    )
    
class Scene:
    def __init__(self, program: ShaderProgram):
        self.program = program
        self.depth = True

        # All primitives (triangles) vertices
        self.batch = pyglet.graphics.Batch()
        self.objects = []

        for x in range(-200, 201, 40):
            for z in range(-200, 201, 40):
                cube(self.program, self.batch, Vec3(x, 0.0, z))
        
    def insert(self):
        ...

    def on_pressed(self, symbol: int):
        if symbol == 117: # U-key
            self.depth = not(self.depth)

    # Enable opengl features
    def start(self):
        if self.depth:
            pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)

    # Disable opengl features
    def end(self):
        pyglet.gl.glDisable(pyglet.gl.GL_DEPTH_TEST)

    def draw(self):
        self.start()
        self.batch.draw()
        self.end()

class Window(pyglet.window.Window):
    def __init__(self):
        super().__init__(vsync=True, width=700, height=500, resizable=True, caption='Simulations')
        self.set_minimum_size(10, 10)

        # Setup shader
        self.setup()
        # Setup camera
        self.camera = Camera()
        self.scene = Scene(self.program)

        # Create debug info text
        self.info = pyglet.text.Label('',
            font_name='Arial',
            font_size=15,
            multiline=True,
            width=2000,
            x=0, y=self.height,
            anchor_x='left', anchor_y='top'
        )

        self.add_hoocks()
        self.lock = False

    def update_info(self, delta: float):
        try:
            fps = 1//delta
        except: 
            fps = 0

        pos = list(floor(self.camera.position))
        rot = list(map(lambda x: floor(degrees(x)), [self.camera.pitch, self.camera.yaw]))

        self.info.y = self.height
        fv = self.camera.fov
        self.info.text = f"FPS: {fps} \nPosition: {pos} \nRotation: {rot} \nFov: {fv}"

    # Update mouse lock
    def update_lock(self, delta):
        self.set_exclusive_mouse(self.lock)

    # Add update hoocks
    def add_hoocks(self):
        pyglet.clock.schedule(self.update_info)
        pyglet.clock.schedule_interval(self.update_lock, interval=1/12)
        pyglet.clock.schedule(self.camera.update)
    
    # Setup vertex and fragment shaders
    def setup(self):
        with open('vertex.glsl') as file:
            vert_shader = Shader(file.read(), 'vertex')
        with open('fragment.glsl') as file:
            frag_shader = Shader(file.read(), 'fragment')
        self.program = ShaderProgram(vert_shader, frag_shader)

    # Keyboard events
    def on_key_press(self, symbol, _modifiers):
        if self.lock:
            self.scene.on_pressed(symbol)
            self.camera.on_pressed(symbol)

        # If F11
        if symbol == 65480:
            self.set_fullscreen(not(self.fullscreen))
            self.set_exclusive_mouse(False)

        # If ESC
        if symbol == 65307:
            self.lock = not(self.lock)

    def on_key_release(self, symbol, _modifiers):
        self.camera.on_released(symbol)

    # Mouse events
    def on_mouse_motion(self, x, y, dx, dy):
        if self.lock:
            self.camera.on_motion(dx, dy)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.lock:
            self.camera.on_scroll(scroll_y)

    def on_draw(self):
        # Clear screen
        self.clear()

        self.program['view'] = self.camera.view()
        self.program['projection'] = self.camera.projection(self.width, self.height)

        # Render vertices
        
        self.scene.draw()
        self.info.draw()

window = Window()
pyglet.app.run()