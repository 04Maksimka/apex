Switch language

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/04Maksimka/AstraGeek/blob/main/README.md)
[![ru](https://img.shields.io/badge/lang-ru-green.svg)](https://github.com/04Maksimka/AstraGeek/blob/main/README.ru.md)

# 🌌 AstraGeek. Star maps

This is a project for AstraGeek astronomy online school.
Here you can find some software for building star maps.

On the [website](https://skychart.astrageek.ru/) of this AstraGeek project you are able to create classic skycharts and star sky maps.

Also visit [astrageek.ru](https://astrageek.ru/) for educational videos on astronomy and related topics.

---

## Release plan

1. Stereographic projection of the starry sky (skychart) according to a 
   given geographical position and time. Also available is the representation of planets, great circles (ecliptic, celestial equator and galactic equator). Available to display horizontal and equatorial coordinate grid, cardinal directions. For example, here the [site](https://skyatlas.app/star-charts/) we were targeting.

2. Add plotting particular parts of the sky using pinhole projection mode. 
   This mode provides all the same features listed in 0.1, but in a different sky projection. It's available to plot constellations by the name, set FOV, camera rotation angle and size of the resulting image.

3. Animations of planets' transits (gif and static image sequences)

4. Add precession of the Earth's rotation

---

## Features

1. Stereographic projection of the entire sky available at specified location and time
2. Pinhole projection for a specific small area of the sky at specified constellation direction
3. You can add various additional reference elements, such as a coordinate grids, coordinate great circles (ecliptic, galactic and celestial equator), cardinal directions, zenith point, and celestial poles.
4. You can add the outlines of all visible constellations, selected constellations, and the names of each visible constellation to the image.

---

## Examples

Pinhole projection example (without a legend) with parameters: ...

<img alt="image" src="https://github.com/user-attachments/assets/c73f3266-20ec-4617-b763-e1647df4d081" style="max-width: 100%; height: auto;" />

Full: [pinhole.pdf](https://github.com/user-attachments/files/24474532/pinhole_local_logo.pdf)


Stereographic projection example (without a legend) with parameters: ...

<img alt="image" src="https://github.com/user-attachments/assets/dfd66621-1e12-43cb-b6c1-06ad275bdd12" style="max-width: 100%; height: auto;" />

Full: [stereographic.pdf](https://github.com/user-attachments/files/24474544/polar_scatter_local_logo.pdf)

---

## How to use


**If wou want to generate new maps by yourself, follow the documentation section below**

You can use the ready-made sets of starry sky maps that we have already generated. To do this, you need:

1. Follow the [link](https://drive.google.com/drive/folders/1AfBc7pkqLH_65TMAeXvpzzzqrLcVKNFO?usp=sharing)
2. Download pinhole_samples archives.zip and samples.zip with pinhole camera mode maps and skycharts, respectively

Inside each folder there are maps of the starry sky with tasks grouped by numbers. 

There are two folders inside the pinhole_samples folder:

1. **сonstellations** - maps with a specific central constellation, for each of the 88 constellations
2. **random_sky** - maps with an arbitrary central constellation, 10 examples

The 100 skycharts for random date and place are grouped inside the samples folder.

Each group consists of three files:

1. For a student without planets - _student.pdf_
2. For a student with planets - _student_with_planets.pdf_
3. For the teacher - _teacher.pdf_

Each file consists of two pages: on the first there are tasks for the map, on the second there is the map itself.

The student's file contains only assignments and a "bare" map. The file for the teacher contains all the answers and a completed map.

---

## Documentation

| Section          | Link                                                                                      |
| ---------------- |-------------------------------------------------------------------------------------------|
| Learn More       | [Usage documentation](https://04maksimka.github.io/AstraGeek/) |
| Project on GitHub| [GitHub Repo](https://github.com/04Maksimka/AstraGeek)                                    |
| Submit Issue     | [Report](https://github.com/04Maksimka/AstraGeek/issues/new)                              |

---
