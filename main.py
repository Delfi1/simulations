import typing
import pyglet
from math import *
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.math import *
import time

from objects import *

# Global pressed buttons
class Buttons:
    def __init__(self):
        self.pressed = set()
        self.just_pressed = set()
        self.released = set()

    def is_pressed(self, key: int) -> bool:
        return key in self.pressed

    def is_just_pressed(self, key: int) -> bool:
        return key in self.just_pressed

    def is_released(self, key: int) -> bool:
        return key in self.released

    def clear(self):
        self.just_pressed.clear()
        self.released.clear()

class Camera:
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

    # forward rotation vector
    def forward(self) -> Vec3:
        return Vec3(cos(self.pitch) * sin(-self.yaw), sin(self.pitch), cos(self.pitch) * cos(-self.yaw))

    # Only x-z plane move vector
    def horizontal_forward(self) -> Vec3:
        return Vec3(cos(self.pitch) * sin(-self.yaw), 0.0, cos(self.pitch) * cos(-self.yaw)).normalize()

    def right(self) -> Vec3:
        return Vec3(cos(-self.yaw), 0.0, -sin(-self.yaw))

    def update(self, delta: float):
        global buttons

        speed = self.speed
        # If ctrl - double speed
        if buttons.is_pressed(65507):
            speed *= 2

        # Wasd-movement
        if buttons.is_pressed(119):
            forw = self.horizontal_forward()
            self.position += forw * speed * delta
        if buttons.is_pressed(97):
            right = self.right()
            self.position += right * speed * delta
        if buttons.is_pressed(115):
            forw = self.horizontal_forward()
            self.position -= forw * speed * delta
        if buttons.is_pressed(100):
            right = self.right()
            self.position -= right * speed * delta
        
        # Down-Up-movement
        if buttons.is_pressed(32):
            self.position += Vec3(0.0, 1.0, 0.0) * speed * delta
        if buttons.is_pressed(65505):
            self.position += Vec3(0.0, -1.0, 0.0) * speed * delta

        # If F-scroll
        if buttons.is_pressed(102):
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
    
    def on_motion(self, dx, dy):
        self.motion += Vec2(dx, dy)

    def on_scroll(self, dy):
        self.scroll += dy

    # Y-axis flipped view-matrix
    FLIP = Mat4(
        a=1, b=0, c=0, d=0,
        e=0, f=-1, g=0, h=0,
        i=0, j=0, k=1, l=0,
        m=0, n=0, o=0, p=1,
    )

    # Flipped view matrix
    def view(self) -> Mat4:
        return self.FLIP @ Mat4.from_translation(self.position)
    
    # Camera projection matrix
    def projection(self, width: int, height: int) -> Mat4:
        return Mat4.perspective_projection(
            width/height, z_near=0.1, z_far=10000, fov=self.fov
        ).rotate(-self.pitch, Vec3(1.0, 0.0, 0.0)).rotate(self.yaw, Vec3(0.0, 1.0, 0.0))

class Scene:
    def __init__(self):
        self.camera = Camera()
        self.objects: typing.List[Object] = list()
        self.batch = pyglet.graphics.Batch()

        self.init_shader()

    def insert(self, object: Object):
        object.setup(self.program, self.batch)
        self.objects.append(object)

    # Load shaders
    def init_shader(self):
        with open('vertex.glsl') as file:
            vert_shader = Shader(file.read(), 'vertex')
        with open('fragment.glsl') as file:
            frag_shader = Shader(file.read(), 'fragment')
        self.program = ShaderProgram(vert_shader, frag_shader)

    # Update all objects
    def update(self, delta: float):
        # Update camera and objects
        
        self.camera.update(delta)
        for obj in self.objects:
            obj.tick(delta)

    # Begin frame states
    def begin(self):
        pyglet.gl.glEnable(pyglet.gl.GL_DEPTH_TEST)

    # End frame states
    def end(self):
        pyglet.gl.glDisable(pyglet.gl.GL_DEPTH_TEST)

    # Make Frame (Batch) and draw
    def draw(self, width: int, height: int):
        self.program['view'] = self.camera.view()
        self.program['projection'] = self.camera.projection(width, height)

        self.begin()
        self.batch.draw()
        self.end()

class Window(pyglet.window.Window):
    def __init__(self):
        super().__init__(resizable=True, vsync=True, width=700, height=500, caption="Simulations")
        self.set_minimum_size(5, 5)

        self.scene = Scene()
        for x in range(0, 401, 40):
            self.scene.insert(Cube(Vec3(x, 0.0, 0.0)*8, Vec3(1.0, 1.0, 1.0)*(400-x)/40))
        self.lock = False

        self.info = pyglet.text.Label('',
            font_name='Arial',
            font_size=15,
            multiline=True,
            width=2000,
            x=0, y=self.height,
            anchor_x='left', anchor_y='top'
        )

        self.add_hoocks()

    # Update debug info
    def update_info(self, delta: float):
        try:
            fps = 1//delta
        except: 
            fps = 0

        pos = list(floor(self.scene.camera.position))
        rot = list(map(lambda x: floor(degrees(x)), [self.scene.camera.pitch, self.scene.camera.yaw]))

        self.info.y = self.height
        fv = self.scene.camera.fov
        self.info.text = f"FPS: {fps} \nPosition: {pos} \nRotation: {rot} \nFov: {fv}"

    def update(self, delta: float):
        global buttons
        self.scene.update(delta)
        buttons.clear()
    
    # Update mouse lock
    def update_lock(self, delta):
        self.set_exclusive_mouse(self.lock)

    def add_hoocks(self):
        pyglet.clock.schedule(self.update_info)
        pyglet.clock.schedule(self.scene.update)
        pyglet.clock.schedule_interval(self.update_lock, 1/12)

    def on_key_press(self, symbol, _modifiers):
        global buttons
        if buttons.is_pressed(symbol):
            buttons.just_pressed.add(symbol)
        buttons.pressed.add(symbol)

        # If F11 - fullscreen
        if symbol == 65480:
            self.set_fullscreen(not(self.fullscreen))
            self.set_exclusive_mouse(False)

        # If ESC - mouse lock
        if symbol == 65307:
            self.lock = not(self.lock)

    def on_key_release(self, symbol, _modifiers):
        buttons.pressed.remove(symbol)
        buttons.released.add(symbol)

    # Mouse events
    def on_mouse_motion(self, x, y, dx, dy):
        if self.lock:
            self.scene.camera.on_motion(dx, dy)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.lock:
            self.scene.camera.on_scroll(scroll_y)

    # Clear screen and draw scene
    def on_draw(self):
        self.clear()
        self.scene.draw(self.width, self.height)
        self.info.draw()

buttons = Buttons()
window = Window()
pyglet.app.run()