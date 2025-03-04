2/17

We have finalized our project proposal and presented to the professor. 

Some of the feedback we got back:

You need to adjust the formatting for your proposal to be suitable in PDF format, it’s clear that you use a markdown file, but your sections and headings should not have that kind of syntax. Your current format is unacceptable right now. 
Use drawing software for Block diagram, hand drawings do not look professional in what is supposed to be professional documentation. 
I would quantify your first high level requirement with force to some degree.
The sensing subsystem is a core feature in this project and will be scrutinized the most. Please finalize your sensors subsystem design and quantify these requirements 
Tolerance analysis is not detailed enough, math and some simulation or something should be involved here 
Develop your ethics and safety section more , pull quotes from these policies you’re mentioning that are relevant to your project
You need to have references 



2/24

We have finalized our parts list and initial design. 

We have also expanded on our tolerance analysis and are confident that our design should withstand the forces it will be subjected to.

We plan to use the 0-100lb flexiforce force sensing resistor (8″ FlexiForce 0-100lb. Resistive Force Sensor (id: 3102_0))

The sensing area is a 0.375” diameter circle. 

This gives us an area of 0.11045 in^2

We will have a pad of area 5 in^2 placed to distribute the force of the blows. 

0.11045/5 = 0.022 = 2.2% of the force is directed to the sensor itself. However this is in a perfect scenario where all of the force is distributed evenly, however in most practical scenarios this won’t be the case. 

This is why we are using a 5in^2 1in thick piece of memory foam to help reduce the force even further. 

We can calculate the force reduced by the foam by treating it like a spring. 

k = (E x A) / t

E = 30kPa (average compressive modulus for low-density memory foam)
A = 5 in^2 = 0.00323 m^2
t = 1 in = 0.0254 m

k = (30,000 x 0.00323) / 0.0254 = 3189 N/m

To calculate the force transmitted through we will use a linear spring model

F = k x t

3819 x 0.0254 = 97 N = 21.8 lbs

This means at full compression, the foam pad absorbs 22lbs of force, which will help dampen the peaks and reduce the likelihood of damage to the sensor. 