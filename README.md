#Towards Black Box Testing of Android Apps

##Description
BBoxTester is a framework able to generate code coverage reports and produce 
uniform coverage metrics in testing of the Android applications when the source
code of them is not available.

This work has been done at the University of Trento.




##Publication
The results of our research will be presented at the 2nd International Workshop 
on Software Assurance (SAW '15) to be held in conjunction with the 
10th International Conference on Availability, Reliability and Security 

Currently, 
please use the following bibtex reference to cite our paper:

```
@inproceedings{BBoxTester_Zhauniarovich2015, 
    author={Zhauniarovich, Yury and Philippov, Anton and Gadyatskaya, Olga and Crispo, Bruno and Massacci, Fabio},
    title={Towards Black Box Testing of Android Apps}, 
    booktitle={2015 Tenth International Conference on Availability, Reliability and Security (ARES)},
    year={2015}, 
    month={August}, 
    pages={to appear}
}

``` 


##Repository Description
BBoxTester folder contains main resources of the application, while 
BBoxTester_Instr_Sources directory stores only code for the auxiliary classes
which are required for application operation.

In BBoxTester folder:

1. Scripts main_activity_strategy.py, main_intents_strategy.py and 
monkey_run_one_apk.py contain examples we used for experiments.
2. bboxtester.py shows different options how the tool can be used.
3. running_strategies.py describes the strategies currently implemented for
the application testing.
4. bboxcoverage.py contains the main class.



##Dependencies
1. [Apktool](https://github.com/iBotPeaches/Apktool) released under Apache-2.0 
License.
2. [dex2jar](https://github.com/pxb1988/dex2jar) released under Apache-2.0 
License.
3. [Emma](http://emma.sourceforge.net/) released under Common Public Lisence.
4. aapt, dx and zipalign are parts of Android Open Source Project and released under
Apache-2.0 Lisence.



##License
The tool is distributed under Apache-2.0 license. The citation of the paper is 
highly appreciated. 
