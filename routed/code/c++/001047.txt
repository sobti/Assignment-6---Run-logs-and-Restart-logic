#include <cmath>
#include <cstdlib>
#include <cstdio>

#include <scratch/particle.hpp>

namespace scratch {
  particle::particle(const GLfloat elapsed)
  {
    this->rate = ((float) rand()) / ((float) RAND_MAX) * 0.1;

    this->x = ((float) rand()) / ((float) RAND_MAX);
    this->y = ((float) rand()) / ((float) RAND_MAX);

    reset(elapsed);
  }

  void particle::reset(GLfloat elapsed)
  {
    spawned = elapsed;
    this->z = 0.5f + ((float) rand()) / ((float) RAND_MAX);
  }

  void particle::update(GLfloat elapsed)
  {
    auto age = elapsed - spawned;
    double distance = age * rate;

    z -= distance;

    if (z < 0) reset(elapsed);
  }
}
