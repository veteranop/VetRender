# FCC Archive Webscraping
Code to webscrape data from the Federal Communications Commission (FCC)'s Universal Licensing Archive System. 
## Built With
- Python 2.7
- Selenium 3.7.0 & ChromeDriver
## Getting Started
### Preresquisites
- Python 2.7 (Version used for CS101 @ Duke) 
- An IDE 
- Selenium & Webdriver (i.e. Chrome, FireFox, Safari) extension
- xlrd (to read in data from excel spreadsheet database)
- xlwt (to generate excel spreadsheet output)
#### Things to Note
##### Operating System & Browser
This webscraper was built on a Mac OS. If you're using another operating system, the Windows command line is different from that of terminal for Mac OS X. (Working on instructions for other operating systems and browsers)

This webscraper was built using ChromeDriver. If you want to use a different browser you will need to install the appropriate webdriver extension. 
##### Python 2.7 vs Python 3 and handling non-ASCII characters
This webscraper was built using Python 2.7, which does not easily read unicode strings. At present, this webscraper is not able to scrape data for 1510 companies whose names have non-ascii characters. It is recommended to explore if it is better to switch to Python 3 which has more unicode support. 

### Installing
#### Python 2.7 (if you followed the Eclipse installation guide below you can skip this step)
You can download from [python.org](https://www.python.org/downloads/) itself. Note that python comes pre-installed on Mac OS X. 
#### IDE
- [PyCharm](https://www.jetbrains.com/pycharm/)
- [Eclipse](https://docs.google.com/document/d/1LgylwTTQiDQpF8kz0_L068G1jE8IYSIcQk-vlwcbUvU/edit) - installation guide for CS101
#### Selenium, xlrd & xlwt
If you have already installed python or if you are using Mac OS X, it is easiest to use ```pip``` on the command line. 
First, open terminal and type ```python get-pip.py```.

To install selenium, type ```pip install selenium```. If it doesn't work, try ```sudo easy_install selenium ```.

To install the xlrd & xlwt packages, type ```pip install xlrd``` and ```pip install xlwt```.

You will have to manually install your webdriver extension. For ChromeDriver, download the latest version [here](https://sites.google.com/a/chromium.org/chromedriver/downloads) and unzip the folder.

After unzipping your folder, open terminal and type in the following commands as shown below:

<p><img width="638" alt="screen shot 2018-02-02 at 10 08 17 pm" src="https://user-images.githubusercontent.com/22549537/35737202-bc386d78-0865-11e8-806d-c9225aaa1ca2.png"></p>

*ScreenShot from Youtube: AutomationTuts*

[This video](https://www.youtube.com/watch?v=XFVXaC41Xac), which the screenshot was taken from, shows you how to install and setup both Selenium and ChromeDriver on a Mac OS. 
  
#### Cloning or Downloading this Reposistory
In this GitHub Repository, click 'Clone or Download':
<p><img width="446" alt="screen shot 2018-02-02 at 7 59 23 pm" src="https://user-images.githubusercontent.com/22549537/35732222-99d93e68-0853-11e8-837e-82e40b77a0ba.png"></p>

If you're not familiar with Github and cloning repositories, you can simply click 'Download ZIP', unzip the folder, and open the **inner directory 'WebScraping' on your IDE**. Importantly, make sure that all the python modules are in the same directory on your IDE. 

## Running the Web Scraper
### Overview
If you understand these already (or are just lazy) just skip to the next section on what code snippets you have to amend.

#### Stating the file path
Basically, whenever you are opening a file, you will need to reference the path of your directory. 

It is usually easiest if the file is in your current directory, as you simply have to state the file name, for example:
```
data = open_workbook('data.xlsx') 
```
If the file is located in another directory, you will need to state the file path, for example:
```
data = open_workbook('/Users/alethea/Documents/data.xlsx') 
```
However with ChromeDriver you will need to state where your ChromeDriver file is located, for example:
```
chromedriver_path = '/Users/alethea/Documents/chromedriver'
driver = webdriver.Chrome(executable_path=chromedriver_path)
```
Note that if you did not change your ChromeDriver file location it will still be in your downloads folder!
#### Code crashing?
Considering the fact that there are 4382 companies, you will mostly encounter TimeOutErrors. 

Fret not, the code has been designed such that in such an event, you can just run the code on companies you have not searched yet while retaining all previously scraped data. The code saves the output data spreadsheet each time it has successfully scraped data for one company. 
### What to amend in the code to work on your local machine
You only need to amend the following lines in **WebScraperMain.py**:
- **Line 149**: change ```chromedriver_path = '/Users/alethea/Documents/chromedriver'``` to state your ChromeDriver file location
- **Line 151**: change ```data = open_workbook('data.xlsx')``` to state the file path of the excel workbook of licensees if it is not in your current directory
- **Lines 70 & 184**: change ```wb.save('/Users/alethea/Downloads/Spreadsheet_test.xls')``` to state which directory you want your data output to be located in. 
- **Line 153**: **state the file path of your output data in** ```visited_file = open_workbook('/Users/alethea/Documents/Spreadsheet_test.xls')``` **which is the same as the one stated in Lines 70 & 184**. This will make your life a lot easier in the event the code crashes.

Whenever you are reading an excel workbook, make sure it is a ```.xlsx``` file and not a ```.xls``` file. To change it you can simply rename it. 

**Finally, run WebScraperMain.py to scrape the data!**

## The Output Data
Sheet 1 contains all the scraped data.

Sheet 2 contains two column lists. The first contains a list of all subsidiary companies that returned results, and the second contains a list of those that did not return any results.

### Cleaning Up the Output Data
This webscraper does not output the data in a sorted order, and does not autofit the column widths in the spreadsheet. 

To sort the data lexicographically by the subsidiaries, click ```Data``` --> ```Sort``` and you should see this:
<img width="694" alt="screen shot 2018-02-02 at 10 27 23 pm" src="https://user-images.githubusercontent.com/22549537/35737959-5043621e-0868-11e8-8d5a-ec034e30f897.png">

Select 'Subsidiary' under the Column tab and click ```ok```. 

To autofit the column width, select all using Command-A, click ```Home``` --> ```Format``` --> ```AutoFit Column Width```.
