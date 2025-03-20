#version 330 core

in vec4 vertex_colors;
out vec4 outColor;

void main()
{
    outColor = vertex_colors;
}