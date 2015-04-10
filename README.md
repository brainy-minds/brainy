<p align="center"><img src="https://github.com/pelkmanslab/brainy/raw/master/ui/web/assets/images/brainy_logo.png" alt="logo" height="121" width="121"></p>

##About *brainy*

*brainy* is a nimble workflow managing tool, at the core of [iBRAIN](https://github.com/pelkmanslab/iBRAIN/) functionality. It allows creation of projects according to the expected framework layout. It also oversees the execution of the projects and provides monitoring of any relevant progress of the conducted computation.

##iBRAIN

iBRAIN is a software framework for scientific computation primarily applied for BigData extraction and analysis in context of HPC and HTS as well as large bioinformatical analysis.

##Documentation

A really good place to understand what is `brainy` is to read the *user manual*:

  * [User manual](https://github.com/pelkmanslab/brainy/wiki/User-Manual)
  * [Developer Documentation](https://github.com/pelkmanslab/brainy/wiki/Developer-Documentation)
   
  > Tip: get help about the commands you need by saying `brainy help` or `brainy help project`


##Getting started

Create you first project

```
brainy create project PureAwesomeness --from demo
```

Go inside the project folder and adjust settings in your pipelines. Afterwards run the project.

```
cd PureAwesomeness
# Adjust settings in .brainy <project settings> and hello.br <pipe description> YAML files
brainy run project
```

To see the report in your local web browser, do 
```
brainy ui serve
```

If things are looking good, continue by submitting your project into the *cloud*. Find out how to do this in the [Cloud](https://github.com/pelkmanslab/brainy/wiki/User-Manual#Cloud) section of the brainy's User Manual. 

##Installation

> On Ubuntu (debian): sudo apt-get install python-setuptools git && sudo easy_install pip

> On Mac: brew install libyaml

>It is strongly recommended to use [conda](http://conda.pydata.org/docs/) as python 2.7+ environment.

The package is available on [PyPI](https://pypi.python.org/pypi/brainy-mind/).


```
pip install brainy-mind
```

To get the bleedding edge version you have to clone the repository and install brainy in developer mode from local folder:

```
cd && git clone https://github.com/pelkmanslab/brainy
cd brainy && pip install -e .
```

Once installed, inspect the state of configuration in `~/.brainy/` folder.

Remember that you can generate `~/.brainy/config` from the template again by

```
brainy init config
```

You will have to edit the template that has been copied according to your cluster scheduler settings and so on.

> Supported OS/platforms are **Linux** and **Mac OSX**.

##Tests

To run nose tests navigate into

```
cd tests && nosetests -s
```
