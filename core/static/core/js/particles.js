// particles-init.js

particlesJS("particles-js", {
    "particles": {
      "number": {
        "value": 80,
        "density": {
          "enable": true,
          "value_area": 1000
        }
      },
      "color": {
        "value": ["#6a5acd", "#7b68ee", "#8a2be2", "#9370db"]
      },
      "shape": {
        "type": "round"
      },
      "opacity": {
        "value": 0.9,
        "random": true,
        "anim": {
          "enable": true,
          "speed": 1.5,
          "opacity_min": 0.1,
          "sync": false
        }
      },
      "size": {
        "value": 4,
        "random": true
      },
      "line_linked": {
        "enable": true,
        "distance": 150,
        "color": "#7b68ee",
        "opacity": 0.3,
        "width": 1
      },
      "move": {
        "enable": true,
        "speed": 2,
        "direction": "none",
        "random": false,
        "straight": false,
        "out_mode": "bounce",
        "bounce": true,
        "attract": {
          "enable": false
        }
      }
    },
    "interactivity": {
      "detect_on": "canvas",
      "events": {
        "onhover": {
          "enable": true,
          "mode": "grab"
        },
        "onclick": {
          "enable": true,
          "mode": "push"
        },
        "resize": true
      },
      "modes": {
        "grab": {
          "distance": 130,
          "line_linked": {
            "opacity": 0.5
          }
        },
        "push": {
          "particles_nb": 4
        }
      }
    },
    "retina_detect": true
  });
  