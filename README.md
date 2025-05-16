# tvcp
Code for IISE paper (under review)  
Time-Varying Capacity Planning for Designing Large-Scale Homeless Care Systems  
Graham Burgess (Lancaster University, UK), Dashi Singham (Naval Postgraduate School, US), Luke Rhodes-Leader (Lancaster University, UK)  

To use this code, clone the repository to your local disk. For successful use, it is important to work within a new conda environment which has all the necessary Python packages installed.
One way of setting this up (for free) is as follows: 
- Install miniconda ([https://www.anaconda.com/docs/getting-started/miniconda/install])  
- Clone the tvcp repository to your local machine.  
- In the command line, navigate to this repository, activate miniconda, ensure conda-forge is available and create a conda environment with the required dependencies:   
  $ cd ~/GitHub/tvcp
  
  $ source ~/miniconda3/bin/activate
  
  $ conda config --add channels conda-forge

  $ conda create -n tvcp jupyter=1.1.1 numpy=2.2.5 simpy=4.1.1 matplotlib=3.10.3 pandas=2.2.3 scipy=1.15.2 pyomo=6.9.2 ipopt=3.14.17 glpk=5.0
  
- Activate this environment and open jupyter notebook
  $ conda activate tvcp
  
  $ jupyter notebook
  
- Open the 'Numerical results.ipynb' notebook to study results or explore other files.
