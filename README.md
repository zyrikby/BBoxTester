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


##Usage
Our tool consists of two parts: a server and a client. The server side of
StaDynA is a Python program that interacts with a static analysis tool. 
Currently, StaDynA uses AndroGuard as a static analyzer. The client side is the
code run either on a real device or on an emulator.

The instructions how to build client side can be found in the corresponding 
folder.

To run the analysis of an Android application, after connecting a device running
client side, execute the server side Python script:

```
python stadyna.py -i <inputApk> -o <resultFolder>
```

where *inputApk* is a path to the apk file to be analyzed, and *resultFolder* is
the path where the results of the analysis will be stored.


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
