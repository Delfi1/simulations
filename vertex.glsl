#version 330 core

layout(location = 0) in vec3 vertices;
layout(location = 1) in vec4 colors;
out vec4 vertex_colors;

uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * vec4(vertices, 1.0f);
    vertex_colors = colors;
}