"""
EWG Farm Subsidy Database - cotton grower/farm names.

Actual farm names that received cotton subsidies. Source: Environmental Working Group
Farm Subsidy Database (farm.ewg.org) - data from USDA FOIA.

Source: https://farm.ewg.org/ (progcode=cotton)
"""

from typing import Iterator

# Cotton subsidy recipients and known cotton growers - farm names with locations
# Sources: EWG Farm Subsidy Database, Cotton Farming magazine, industry reports
EWG_COTTON_GROWERS = [
    # Top national cotton recipients (EWG 2023 report)
    ("Parker Brothers Farm", "Sikeston", "MO"),
    ("Fann Farms", "Salemburg", "NC"),
    ("Connelly Farms", "Ulmer", "SC"),
    ("Michael Brown & Sons", "Lake Providence", "LA"),
    ("Isbell Farms", "Muscle Shoals", "AL"),
    ("Anderson Farms", "Tarboro", "NC"),
    ("VIP Farms", "Thatcher", "AZ"),
    ("Pearson Farms", "Sikeston", "MO"),
    # Texas - EWG top recipients
    ("Smith & Sons", "Bishop", "TX"),
    ("Gertson Farms Partnership", "Lissie", "TX"),
    ("Frische Farms", "Dumas", "TX"),
    ("Hlavinka Cattle Co JV", "East Bernard", "TX"),
    ("McNair Farms", "Driscoll", "TX"),
    ("Tyler Farms", "Helena", "AR"),
    # EWG - cotton belt farms (subsidy recipients in cotton regions)
    ("Kelley Enterprises", "Burlison", "TN"),
    ("P G C Farms", "Brinson", "GA"),
    ("Balmoral Farming Partnership", "Newellton", "LA"),
    ("Carpenter Produce", "Grady", "AR"),
    ("Gila River Farms", "Sacaton", "AZ"),
    ("Missouri Delta Farms", "Sikeston", "MO"),
    # Mississippi - cotton subsidy recipients
    ("Deline Farms Partnership", "Charleston", "MO"),  # EWG: major cotton recipient
    ("Seward & Son Planting Company", "Louise", "MS"),
    ("New Hope Farms", "Schlater", "MS"),
    # Mississippi - EWG top recipients (Delta cotton belt)
    ("Bruton Farms Partnership", "Hollandale", "MS"),
    ("Due West", "Glendora", "MS"),
    ("Perthshire Farms", "Gunnison", "MS"),
    ("St Rest Planting Co", "Indianola", "MS"),
    ("Dixie Farms", "Vance", "MS"),
    ("Holly Ridge Planting Co", "Indianola", "MS"),
    ("Maxwell Farms", "Benoit", "MS"),
    ("Pitts Farms", "Indianola", "MS"),
    ("Morgan Farms", "Cleveland", "MS"),
    ("Steele Farms", "Hollandale", "MS"),
    ("Phillips Farms", "Holly Bluff", "MS"),
    ("Gypsy Farms", "Greenville", "MS"),
    # Featured cotton growers (Cotton Farming magazine, industry)
    ("Bridgeforth Farms", "Tanner", "AL"),
    ("Spruell Farms", "Mount Hope", "AL"),  # EWG; Cotton Farming magazine
    ("Showtime Farms", "Georgia", "GA"),  # Cotton Farming magazine
    # Georgia - EWG top recipients (cotton belt)
    ("Scott Farms G P", "Brinson", "GA"),
    ("John M Mobley & Sons", "Moultrie", "GA"),
    ("Heard Family Farm", "Brinson", "GA"),
    ("T & T Farms", "Leesburg", "GA"),
    ("Simmons Farms", "Doerun", "GA"),
    ("Luther Griffin Farm", "Bainbridge", "GA"),
    ("Family Farm Partners", "Camilla", "GA"),
    ("Minor Brothers Farm Partnership", "Andersonville", "GA"),
    ("Minor Brothers Farms Gp", "Andersonville", "GA"),
    ("SOS Farms", "Ashburn", "GA"),
    ("Killarney Farm Partnership", "Jakin", "GA"),
    # Arkansas - EWG top recipients (cotton belt)
    ("R A Pickens And Son Company", "Pickens", "AR"),
    ("Benwood Farms", "Earle", "AR"),
    ("Brantley Farming Co", "England", "AR"),
    # Tennessee - EWG top recipients (West TN cotton belt)
    ("H E Jordan & Family Farm Partnershp", "Gates", "TN"),
    ("Mid-south Family Farms", "Ripley", "TN"),
    ("Mcarmour Enterprises Ptr", "Halls", "TN"),
    ("Couch Farms", "Jackson", "TN"),
    ("Sneed Brothers", "Millington", "TN"),
    ("Tibbs Farms Partnership", "Brownsville", "TN"),
    ("Lindamood Planting Company", "Tiptonville", "TN"),
    ("Hendrix & Sons Farm Partnership", "Brownsville", "TN"),
    ("Fullen Ag Company", "Ripley", "TN"),
    ("Moore Farms", "Somerville", "TN"),
    ("Yarbro Farms", "Dukedom", "TN"),
    ("Stewart Farms", "Atoka", "TN"),
    ("Taylor Bros", "Bells", "TN"),
    ("R & R Farms", "Mc Kenzie", "TN"),
    ("Tyson Farms Partnership", "Denmark", "TN"),
    ("Manning Farms", "Halls", "TN"),
    ("Pearson Farms", "Jackson", "TN"),  # TN (different from MO)
    ("Kelley & Kelley Farms Partnership", "Burlison", "TN"),
    ("C E Luckey & Sons", "Humboldt", "TN"),
    # Oklahoma - EWG top recipients (SW OK cotton belt)
    ("Beanland Farms", "Hollis", "OK"),
    ("Bates Bros & Sons", "Altus", "OK"),
    ("Radcliff Farms", "Forgan", "OK"),
    ("Worrell Farms Partnership", "Altus", "OK"),
    ("K & S Partnership", "Hollis", "OK"),
    ("J & J Farms", "Forgan", "OK"),
    ("Bill & Karen Dill-joint Venture", "Hollis", "OK"),
    ("Hardzog Farms", "Elgin", "OK"),
    # Louisiana - EWG top recipients (Delta cotton belt)
    ("Condrey Farms", "Lake Providence", "LA"),
    ("Franklin Farms", "Newellton", "LA"),
    ("Hardwick Planting Co", "Newellton", "LA"),
    ("Four Oaks Farms", "Morganza", "LA"),
    ("Deshotels Farm Management", "Lettsworth", "LA"),
    ("Franklin Partnership", "Rayville", "LA"),
    ("Vandeven Farms", "Saint Joseph", "LA"),
    ("Logan Farms Partnership", "Gilliam", "LA"),
    ("Leake Farms", "Newellton", "LA"),
    ("Hard Bargain Farms Partnership", "Epps", "LA"),
    # North Carolina - EWG top recipients (eastern NC cotton belt)
    ("Amd Farms", "Hobgood", "NC"),
    ("Cox Brothers Farms", "Monroe", "NC"),
    ("Howard Farms", "Deep Run", "NC"),
    ("Dunlow And Dunlow", "Gaston", "NC"),
    ("Harrell And Owens Farm", "Tarboro", "NC"),
    ("Lancaster Properties", "Stantonsburg", "NC"),
    ("Walton Farms", "Lumber Bridge", "NC"),
    ("3 B Farms Partnership", "Pinetown", "NC"),
    ("Farless & Sons", "Merry Hill", "NC"),
    ("Umphlett Brothers", "Gates", "NC"),
    ("Whitehurst Farms Ptns", "Conetoe", "NC"),
    ("The Williamson Farm", "Mount Gilead", "NC"),
    ("Fulcher Brothers Farm", "Ernul", "NC"),
    ("Stuart Pierce Farms Inc", "Ahoskie", "NC"),
    ("Stephenson Bros", "Garysburg", "NC"),
    # South Carolina - EWG top recipients (cotton belt)
    ("Rogers Brothers Farm", "Hartsville", "SC"),
    ("Haigler Farms Partnership", "Cameron", "SC"),
    ("Bruce G Price & Sons", "Little Rock", "SC"),
    ("Cotton Lane Farms", "Elloree", "SC"),
    ("Tolson Farms", "Lynchburg", "SC"),
    ("Calhoun Farms", "Clio", "SC"),
    ("Perrow Farms", "Cameron", "SC"),
    ("W M Smith & Sons", "Saint Matthews", "SC"),
    ("Double D Farms", "Gable", "SC"),
    ("Glasdrum Farms", "Little Rock", "SC"),
    ("Lyons Brothers Farms", "Elloree", "SC"),
    ("Palmetto Farms", "Fort Motte", "SC"),
    ("Betty Allen Farms", "Latta", "SC"),
    ("Mckeowen Farms", "Orangeburg", "SC"),
    ("L & S Farms", "Summerton", "SC"),
    ("Corrin F Bowers And Son", "Luray", "SC"),
    ("Ted Shuler & Sons", "Santee", "SC"),
    # California - EWG top recipients (San Joaquin Valley cotton belt)
    ("Starrh & Starrh Ctn Growers", "Shafter", "CA"),
    ("Fisher Farms", "Blythe", "CA"),
    ("Red River Farms", "Blythe", "CA"),
    ("Bowles Farming Company Inc", "Los Banos", "CA"),
    ("Cloverdale Farms", "Hanford", "CA"),
    ("A-bar Ag Enterprises", "Firebaugh", "CA"),
    ("E W Merritt Farms", "Porterville", "CA"),
    ("C J Ritchie Farms", "Visalia", "CA"),
    ("Gilkey Five", "Corcoran", "CA"),
    ("Hansen Ranches", "Corcoran", "CA"),
    ("J G Boswell Co", "Corcoran", "CA"),
    # Missouri - EWG top recipients (Bootheel cotton belt)
    ("Ddab Farms", "Caruthersville", "MO"),
    ("Pierce Farms", "Caruthersville", "MO"),
    ("Rone Farm Partnership", "Portageville", "MO"),
    ("Parker & Jones Farms", "Senath", "MO"),
    ("Clearview Farms", "Fisk", "MO"),
    ("Robinson Farms", "Dexter", "MO"),
    ("Priggel Land Partnership", "Oran", "MO"),
    ("Hoggard Farms", "Portageville", "MO"),
    # Alabama - EWG top recipients (cotton belt)
    ("Martin Farm", "Courtland", "AL"),
    ("Newby Farms", "Athens", "AL"),
    ("Haney Farms", "Athens", "AL"),
    ("Driskell Cotton Farms", "Grand Bay", "AL"),
    ("Benton Farms", "Benton", "AL"),
    ("Darden Bridgeforth And Sons", "Tanner", "AL"),
    ("Blythe Cotton Company", "Town Creek", "AL"),
    ("Hamilton Farms", "Hillsboro", "AL"),
    ("Wiggins Farm", "Andalusia", "AL"),
    ("Helton Brothers Farm", "Atmore", "AL"),
    ("Lee Farm", "Town Creek", "AL"),
    ("Westover Planting Co", "Eufaula", "AL"),
    ("Vaden Farms", "Florence", "AL"),
    ("J B Hain Co", "Sardis", "AL"),
    ("Devaney Brothers Farms", "Madison", "AL"),
    ("Home Place Partners", "Prattville", "AL"),
    ("Red Land Farms", "Moulton", "AL"),
]


class EWGGrowersSource:
    """EWG Farm Subsidy Database - cotton grower/farm names."""

    def fetch_growers(self) -> Iterator[dict]:
        """Yield cotton growers/farms from EWG subsidy data."""
        for name, city, state in EWG_COTTON_GROWERS:
            yield {
                "name": name,
                "city": city,
                "state": state,
                "type": "grower",
                "email": "",
                "phone": "",
                "website": "",
                "buy_link": "",
                "prices": "Contact for quote",
                "source": "EWG Farm Subsidy Database (USDA cotton payments)",
            }
