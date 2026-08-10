#pragma once
#include "typed-geometry/types/vec.hh"
#include "typed-geometry/types/pos.hh"

namespace gamedev
{
struct PointLight
{
    alignas(16) tg::pos3 position;
    alignas(16) tg::vec3 color;
    float intensity;
    float radius;
};

struct DirectionalLight
{
    tg::vec3 direction;
    tg::vec3 color;
};

struct AmbientLight
{
    tg::vec3 color;
};
}
