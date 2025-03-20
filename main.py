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

        self.speed = 20.0
        self.scroll_speed = self.speed*4
        self.sensitivity = 0.2
        self.yaw = pi/4
        self.pitch = -radians(40)

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

        if self.scroll:
            forw = self.forward()
            self.position +=  forw * self.scroll_speed * self.scroll 
            self.scroll = 0.0

        # Rotate camera
        self.yaw += radians(self.motion.x) * self.sensitivity
        self.pitch += radians(self.motion.y) * self.sensitivity
        self.pitch = clamp(self.pitch, -pi/2, pi/2)

        self.motion = Vec2()

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
    
    def projection(self, width: int, height: int) -> Mat4:
        return Mat4.perspective_projection(
            width/height, z_near=0.1, z_far=1000, fov=70.0
        ).rotate(-self.pitch, Vec3(1.0, 0.0, 0.0)).rotate(self.yaw, Vec3(0.0, 1.0, 0.0))

class Scene:
    def __init__(self, program: ShaderProgram):
        self.program = program

        # All primitives (triangles) vertices
        self.batch = pyglet.graphics.Batch()
        self.objects = []

        self.cube = self.program.vertex_list_indexed(
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
            batch=self.batch,
            vertices=('f', (
                -10.0, -10.0, 10.0, 10.0, -10.0, 10.0, # 0 1
                -10.0, 10.0, 10.0, 10.0, 10.0, 10.0, # 2 3
                -10.0, -10.0, -10.0, 10.0, -10.0, -10.0, # 4 5
                -10.0, 10.0, -10.0, 10.0, 10.0, -10.0 # 6 7
            )),
            normals=('f', (
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            )),
            colors=('Bn', [255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 0, 255]*2)
        )
    
    def insert(self):
        ...

    # Enable opengl features
    def start(self):
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
            font_size=18,
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
        self.info.text = f"FPS: {fps} \nPosition: {pos} \nRotation: {rot}"

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