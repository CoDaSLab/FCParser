"""

FaaC parser library -- classes and tools for parsing and processing raw network
data and preparing it for further multivariate analysis.

See README file to learn how to use FaaC parser library.

Authors: Alejandro Perez Villegas (alextoni@gmail.com)
     Jose Manuel Garcia Gimenez (jgarciag@ugr.es)
     Jose Camacho (josecamacho@ugr.es)    

Last Modification: 11/Aug/2018

"""

from datetime import datetime, timedelta
from sys import exit
from IPy import IP
import re
import os
import yaml
import glob
import shutil
#import time
from sys import stdin
from collections import defaultdict


#-----------------------------------------------------------------------
# Variable Class
#-----------------------------------------------------------------------

class Variable(object):
    """Single piece of information contained in a raw record.
    
    This is an abstract class, and should not be directly instantiated. 
    Instead, use one of the subclasses, defined for each matchtype of variable:
    - StringVariable    (matchtype 'string')
    - NumberVariable    (matchtype 'number')
    - IpVariable        (matchtype 'ip')
    - TimeVariable      (matchtype 'time')
    - TimedeltaVariable (matchtype 'duration')
    - MultipleVariable  (matchtype 'multiple')
    
    Class Attributes:
        value -- The value of the variable.
    """
    def __init__(self, raw_value):
        """Class constructor.

        raw_value -- Single value, as it is read from the input.
        """
        self.value = self.load(raw_value)

    def equals(self, raw_value):
        """Compares this variable to a given value.
        Returns 1 if the comparison matches; 
                0 otherwise.

        raw_value -- The value to compare with.
        """
        value = self.load(raw_value)
        output = (self.value == value)
        if output:
            return 1
        else:
            return 0

    def belongs(self, start, end):
        """Checks whether this variable belongs to an interval.
        Returns 1 if the variable's value belongs to the interval;
                0 otherwise.
        
        start -- Initial value of the interval (inclusive).
        end   -- Final value of the interval (inclusive).
                 'None' value means infinite.
        """
        start_value = self.load(start)
        end_value   = self.load(end)

        if self.value is None or start_value is None:
            output = False
        elif end_value is None:
            output = (self.value >= start_value)
        else:
            output = (self.value >= start_value and self.value <= end_value)

        return output
        

    def __repr__(self):
        """Class default string representation.
        """
        return self.value.__str__()


class StringVariable(Variable):
    """Variable containing an alphanumeric value.
    """
    
    def load(self, raw_value):
        """Converts an input raw value into a string object.
        Returns: String, if the conversion succeeds;
                 None, if the string is empty or the conversion fails.

        raw_value -- The input raw value.
        """
        if raw_value:
            try:
                value = str(raw_value).strip()
                if not value:
                    value = None
            except:
                value = None
        else:
            value = None
        return value


class NumberVariable(Variable):
    """Variable containing a number.
    """

    def load(self, raw_value):
        """Converts an input raw value into an integer number.
        Returns: Integer number, if the conversion succeeds;
                 None, if the conversion fails.

        raw_value -- The input raw value.
        """
        try:
            value = int(raw_value)
        except:
            #print('\033[33m'+ "Error while processing %s as an int value" %(raw_value) +'\033[m')
            value = None
            
        return value

class RegexpVariable(Variable):
    """Variable containing a regexp match.
    """

    def load(self, raw_value):
        """Converts an input regexp match into a string object.
        Returns: String, if the conversion succeeds;
        None, if the string is empty or the conversion fails.

        raw_value -- regexp match.
        """
        if raw_value:
            try:
                value = str(raw_value).strip()
                if not value:
                    value = None
            except:
                value = None
        else:
            value = None
        return value


class IpVariable(Variable):
    """Variable containing an IP address.
    """
        
    def equals(self, raw_value):
        """Compares this IP address to a given one, OR
        Checks this IP address matchtype.
        Suported matchtypes: 'private', 'public'.
        
        raw_value -- Specific IP address, OR matchtype of IP.
        """
        if self.value is None:
            output = False
        elif raw_value == 'private':
            output = (self.value.iptype() == 'PRIVATE')
        elif raw_value == 'public':
            output = (self.value.iptype() == 'PUBLIC')
        else:
            value = self.load(raw_value)
            output = (self.value == value)

        return output
        
    def load(self, raw_value):
        """Converts an input raw value into a IP address.
        Returns: IP object, if the conversion succeeds;
                 None, if the conversion fails.

        raw_value -- The input raw value, representing a IP address
                     (eg. '192.168.1.1').
        """
        try:
            ipaddr = IP(raw_value)
        except:
            print('\033[33m'+ "Error while processing IP: '%s'" %(raw_value) +'\033[m')
            ipaddr = None
            
        return ipaddr


class TimeVariable(Variable):
    """Variable containing a timestamp value.
    """
    
    def __init__(self, raw_value, tsformat):
        self.value = self.load(raw_value, tsformat)
        
    def load(self, raw_value, tsformat):
        """Converts an input raw value into a timestamp.
        raw_value -- the raw value in string format (eg. '2014-12-20 15:01:02')
        tsformat -- timestamp format
        Returns: Datetime object, if the conversion succeds;
                 None, if the conversion fails.
        """
        try:
            timestamp = datetime.strptime(raw_value, tsformat)
        except:
            print('\033[31m'+ "Error while comparing %s with %s" %(raw_value, tsformat) +'\033[m')
            timestamp = None
             
        # If no year is defined in log_timestamp, current year is set
        try:
            if timestamp.year == 1900:
                timestamp = timestamp.replace(year = datetime.now().year)
        except AttributeError:
            pass
            
        return timestamp


    """ Old implementation   
    def load(self, raw_value):
        if isinstance(raw_value, str):
            try:
                timestamp = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")  
            except:
                timestamp = None
        else:
            try:
                timestamp = datetime.utcfromtimestamp(float(raw_value)/1000)
            except:
                timestamp = None
        return timestamp
    """


class TimedeltaVariable(TimeVariable):
    """Variable containing a time duration.
    The value is a timedelta object.
    """
    def __init__(self, start_value, end_value):
        """Class constructor.

        start_value -- Raw start timestamp.
        end_value   -- Raw end timestamp.
        """
        start_time = super(TimedeltaVariable, self).load(start_value)      # Python3: super().__init__()
        end_time   = super(TimedeltaVariable, self).load(end_value)        # Python3: super().__init__()
        try:
            self.value = end_time - start_time
        except TypeError:
            self.value = None
    
    def load(self, raw_value):
        """Converts an input raw value into a timedelta.
        Returns: Timedelta object, if the conversion succeeds;
                 None, if the conversion fails.

        raw_value -- The time duration, in seconds (eg. 3600),
        """
        try:
            duration = timedelta(seconds = int(raw_value))
        except:
            duration = None
        return duration

    def __repr__(self):
        """Default string representation: number of seconds
        """
        if self.value is not None:
            return str(self.value.total_seconds())
        else:
            return str(None)


class MultipleVariable(object):
    """Multiple variable. Contains a list of variables.
    """
    def __init__(self, variable):
        """Class constructor.

        variable -- Single variable, first in the list.
        """
        self.value = []
        self.value.append(variable)
        
    def equals(self, raw_value):
        """Counts the amount of variables that equal the given value.
        Returns the number of matches.

        raw_value -- Single value to compare with.
        """
        count = 0
        for f in self.value:
            if f.equals(raw_value):
                count += 1
        return count
    
    def belongs(self, start, end):
        """Counts the amount of variables that belong to the given interval.
        Returns the number of matches.

        start -- Initial value of the interval (inclusive).
        end   -- Final value of the interval (exclusive).
                 'None' value means infinite.
        """
        count = 0
        for f in self.value:
            if f.belongs(start, end):
                count += 1
        return count
        
    def __repr__(self):
        """Class default string representation.
        """
        return self.value.__str__()


#-----------------------------------------------------------------------
# Record Class
#-----------------------------------------------------------------------

class Record(object):
    """Information record containing data variables. It is a dictonary of variables.
    
    The variables are defined in the user conf file, section VARIABLES.
    Each variable will be later used to define one or more features.
    
    A record looks like this:
    {flow_id: '4485422', src_ip: '192.168.1.2', src_port: 80, ...}
    
    Class Attributes:
        variables -- Dictionary of variables, indexed by their name.
        
    """
    def __init__(self, line, variables, structured, tsformat, all=False):
        self.variables = {}
        
        # For structured sources
        if structured:
            raw_values = line.split(',')
            #print(raw_values)

            for v in variables:
                try:
                    vType = v['matchtype']
                    vName = v['name']
                    vWhere  = v['where']
                except KeyError as e:
                    raise ConfigError(self, "VARIABLES: missing config key (%s)" %(e.message))    
                try:
                    vMult = v['mult']
                except KeyError:
                    vMult = False
                
                # Validate name
                if vName:
                    vName = str(vName)
                else:
                    raise ConfigError(self, "VARIABLE: empty id in variable")

                # Validate arg
                try:

                    if isinstance(vWhere, list) and len(vWhere) == 2:
                        if vWhere[0]>len(raw_values) or vWhere[1]>len(raw_values):
                             vValue = [None,     None]
                        else:
                            vValue = [raw_values[vWhere[0]], raw_values[vWhere[1]]]
                    else:
                        if vWhere>len(raw_values):
                             vValue = None
                        else:
                            vValue = raw_values[vWhere]

                except (TypeError, IndexError) as e:
                    raise ConfigError(self, "VARIABLES: illegal arg in \'%s\' (%s)" %(vName, e.message))

                except:
                    vValue = None

                variable = list();
                # Validate matchtype
                if vType == 'string':
                    variable.append(StringVariable(vValue))
                elif vType == 'number':
                    variable.append(NumberVariable(vValue))
                elif vType == 'ip':
                    variable.append(IpVariable(vValue))
                elif vType == 'time':
                    variable.append(TimeVariable(vValue, tsformat))
                elif vType == 'duration':
                    if isinstance(vValue, list) and len(vValue) == 2:
                        variable.append(TimedeltaVariable(vValue[0], vValue[1]))
                    else:
                        raise ConfigError(self, "VARIABLES: illegal arg in %s (two-item list expected)" %(vName))
                else:
                    raise ConfigError(self, "VARIABLES: illegal matchtype in \'%s\' (%s)" %(vName, vType))
                    
                # Add variable to the record
                if vMult:
                    self.variables[vName] = MultipleVariable(variable)
                else:
                    self.variables[vName] = variable

        # For unstructured sources

        else:

            for v in variables:
                try:
                    vName = v['name']
                    vWhere = v['where']
                    vMatchType = v['matchtype']
                    if isinstance(vWhere,str):
                        vType = 'regexp'
                        vComp = v['r_Comp']

                except KeyError as e:
                    raise ConfigError(self, "VARIABLES: missing config key (%s)" %(e.message))


                # Validate matchtype
                if vType == 'regexp':

                    try:
                        if all:
                            vValues = vComp.findall(line)
                        else:
                            vV = vComp.search(line)
                            vValues = [vV.group(0)]

                        variable = list();

                        for vValue in vValues:

                            if vMatchType == 'string':
                                variable.append(StringVariable(vValue))

                            elif vMatchType == 'number':
                                variable.append(NumberVariable(vValue))

                            elif vMatchType == 'ip':
                                variable.append(IpVariable(vValue))

                            elif vMatchType == 'time':
                                variable.append(TimeVariable(vValue, tsformat))

                            elif vMatchType == 'duration':
                                if isinstance(vValue, list) and len(vValue) == 2:
                                    variable.append(TimedeltaVariable(vValue[0], vValue[1]))
                                else:
                                    raise ConfigError(self, "VARIABLES: illegal arg in %s (two-item list expected)" %(vName))


                    except:
                        variable = [None]
                else:
                    raise ConfigError(self, "VARIABLES: illegal matchtype in '%s' (%s)" %(vName, vMatchType))


                self.variables[vName] = variable
    
    def __repr__(self):
        return "<%s - %d variables>" %(self.__class__.__name__, len(self.variables))
        
    def __str__(self):
        return self.variables.__str__()


#-----------------------------------------------------------------------
# Feature Class
#-----------------------------------------------------------------------

class Feature(object):
    """Quantitative feature contained in an observation.
    
    This is an abstract class, and should not be directly instantiated. 
    Instead, use one of the subclasses, defined for each matchtype of feature:
    - SingleFeature    (matchtype 'single')
    - MultipleFeature  (matchtype 'multiple')
    - RangeFeature     (matchtype 'range')
    - RegExpFeature    (matchtype 'regexp')
    - DefaultFeature   (matchtype 'default')
    - ListFeature      (matchtype 'list')
    
    Class Attributes:
        value -- The value of the variable.
    """
    def __init__(self, fconfig):
        """Class constructor.

        raw_value -- Single value, as it is read from the input.
        """
        self.fName  = fconfig['name']
        self.fVariable = fconfig['variable']
        self.fValue = fconfig['value']
        self.value = 0

    def add(self, var):
        """Adds a variable to the feature if it is suitable.
        """
        self.value += var.equals(self.fValue)

    def aggregate(self, feature):
        """Adds a feature to the feature.
        """
        if not isinstance(feature, Feature):
            raise AggregateError (self, "Ubale to add %s and %s" %(self.__class__.__name__, feature.__class__.__name__))

        if feature.value is not None:
            self.value += feature.value
        

    def __repr__(self):
        """Class default string representation.
        """
        return self.value.__str__()


class SingleFeature(Feature):
    """Counter of a single value (e.g port 80).
    """

    def __init__(self, fconfig):

        if isinstance(fconfig['value'], list):
            raise ConfigError(self, "FEATURES: illegal value in '%s' (single item expected)" %(fconfig['value']))

        super(SingleFeature, self).__init__(fconfig)



class MultipleFeature(Feature):
    """Counter of several values (e.g ports 80 & 8080).
    """

    def __init__(self, fconfig):

        if not isinstance(fconfig['value'], list):
            raise ConfigError(self, "FEATURES: illegal value in '%s' (list of items expected)" %(fconfig['value']))

        super(MultipleFeature, self).__init__(fconfig)

    def add(self, var):

        for v in self.fValue:
            super(MultipleFeature, self).add(var)


class RangeFeature(Feature):
    """Counter of several values (e.g ports 80 & 8080).
    """

    def __init__(self, fconfig):

        if isinstance(fconfig['value'], list) and len(fconfig['value']) == 2:

            super(RangeFeature, self).__init__(fconfig)

            self.start = self.fValue[0]
            self.end =  self.fValue[1]
            if str(self.end).lower() == 'inf':
                self.end  = None
        else:
            raise ConfigError(self, "FEATURES: illegal value in '%s' (two-item list expected)" %(fconfig['value']))


    def add(self, var):
        self.value += var.belongs(self.start, self.end)



class RegExpFeature(Feature):
    """Counter of reg. expresions, for unstructured data
    """

    def __init__(self, fconfig):
        if isinstance(fconfig['value'], list):
            raise ConfigError(self, "FEATURES: illegal value in '%s' (single item expected)" %(fconfig['name']))

        super(RegExpFeature, self).__init__(fconfig)

        self.r_Comp = fconfig['r_Comp']


    def add(self, var):

        try:
            matchObj = self.r_Comp.match(str(var).replace('[','').replace(']',''))
        except re.error as e:
            raise ConfigError(self, "FEATURES: illegal regexp in '%s' (%s)" %(self.fName, e.message))
        
        if matchObj:
            self.value += 1


        
class DefaultFeature(Feature):
    """Counter of number of variable instances not identified in other features
    """
                
    def add(self, variables, matched_variables):
        
        counter = 0
        
        for variable_name in variables:
            for var in variables[variable_name]:
                if var not in matched_variables and variable_name == self.fVariable:
                    counter += 1
        
        self.value += counter
        
        
class TotalFeature(Feature):
    """Counter of number of variable instances 
    """
                
    def add(self, var):

        self.value += 1

class NullFeature(Feature):
    """Null feature used to identify non-meaningful features in a observation
    """

    def __init__(self):
        super(NullFeature, self).__init__({'name': "Null", 'variable': 'null', 'value': 0})

#-----------------------------------------------------------------------
# Observation Class
#-----------------------------------------------------------------------

class Observation(object):
    """Observation array containing data suitable for the analysis.
    
    An observation array represents one row of data, and consist of a
    number of instances of the defined features. A feature represents
    one column of data. Thus, the input of the multivariate analysis
    engine consist of a N-by-M data matrix (N observations, M features).
    
    The features are defined in the user conf file, section features.
    Each feature is a integer counter defined from a specific variable.
    
    An observation looks like this:
    [0, 1, 0, 0, 2, 0, 0, 0, 3, 1, 0, ...]

    Class Attributes:
        data  -- Array of data values.

    """


    def __init__(self, data, debug=None):

        self.data = data

        
    @classmethod
    def fromRecord(cls, record, FEATURES):
        """Creates an observation from a record of variables.
        record    -- Record object.
        FEATURES -- List of features configurations."""

        data  = [None] * len(FEATURES)      # Data array (counters)
        defaults = []                       # tracks default features
        matched_variables = []              # List of variables from record matching at least one defined feature
        

        for i in range(len(FEATURES)):
            try:
                fType  = FEATURES[i]['matchtype']

                # Validate matchtype
                if fType == 'single':
                    feature = SingleFeature(FEATURES[i])
                elif fType == 'multiple':
                    feature = MultipleFeature(FEATURES[i])
                elif fType == 'range':
                    feature = RangeFeature(FEATURES[i])
                elif fType == 'regexp':
                    feature = RegExpFeature(FEATURES[i])
                elif fType == 'default':
                    feature = DefaultFeature(FEATURES[i])
                elif fType == 'total':
                    feature = TotalFeature(FEATURES[i])
                else:
                    raise ConfigError(cls, "FEATURES: illegal matchtype in \'%s\' (%s)" %(FEATURES[i]['name'], fType))


            except KeyError as e:
                raise ConfigError(cls, "FEATURES: missing config key (%s)" %(e.message))


            # Calculate feature 

            # Iterate through all the features in the conf file. For each iteration, check the matchtype of the variable 
            # involved. Then, check the value of the variable asociated to the feature. If there is a match, the counters
            # of the observations are increased. --> FaaC (Feature as a counter)
            variable = record.variables[FEATURES[i]['variable']]

            data[i]  = feature
            
            for var in variable:
                if var is not None:     # It is necessary to differentiate between var==None (no valid object) and 
                    if var.value is not None:       # var.value==None (valid object but a None in the value field)       
                        if fType == 'default':
                            if i not in defaults:
                                defaults.append(i)
                        else:
                            old_data_value = data[i].value
                            data[i].add(var)    # This method sums 1 or 0 depending if variable satisfies feature value
                            if (data[i].value - old_data_value) > 0 and (var not in matched_variables):
                                matched_variables.append(var)

        # Calculate default features counters
        for d in defaults:
            data[d].add(record.variables, matched_variables)
            

        return cls(data)        

            
    def aggregate(self, obs):
        """ Aggregates this observation with a new one.
            obs -- Observation object to merge with.
        """
        
        try:
            for i in range(len(self.data)):
                self.data[i].aggregate(obs.data[i])
        except IndexError as e:
            raise AggregateError (self, "Unable to aggregate data arrays (%s)" %(e.message))


    def fuse(self, data):
        """ Aggregates this observation with a new one.
            obs -- Observation object to merge with.

        """
        self.data += data


    def zeroPadding(self, N, position=-1):

        try:
            if(position == 0):
                self.data[:0] = [NullFeature()] * N
            elif(position == -1):
                self.data[-1:] = [NullFeature()] * N
            else:
                self.data[position:position] = [NullFeature()] * N
        except:
            raise PaddingError(message="Unsupported position")


    def __repr__(self):
        return "<%s - %d vars>" %(self.__class__.__name__, len(self.data))
        
    def __str__(self):
        return self.data.__str__()


#-----------------------------------------------------------------------
# Exception and Error Classes
#-----------------------------------------------------------------------

class ConfigError(Exception):
    def __init__(self, obj, message=''):
        self.obj = obj
        self.message = message
        self.msg = "ERROR - Config File - %s" %(message)

    def __str__(self):
            return repr(self.msg)

class AggregateError(Exception):
    def __init__(self, obj, message=''):
        self.obj = obj
        self.message = message
        self.msg = "ERROR - Aggregate - %s" %(message)

    def __str__(self):
            return repr(self.msg)

class PaddingError(Exception):
    def __init__(self, obj, message=''):
        self.obj = obj
        self.message = message
        self.msg = "ERROR - Padding - %s" %(message)

    def __str__(self):
            return repr(self.msg)


#-----------------------------------------------------------------------
# Read configuration file
#-----------------------------------------------------------------------

def getConfiguration(config_file):
    '''
    Function to load config file. It is used for general and datasources config. files
    '''
    stream = open(config_file, 'r')
    conf = yaml.safe_load(stream) # conf = yaml.load(stream)
    if 'FEATURES' not in conf:
        conf['FEATURES'] = {}

    stream.close()
    return conf


def loadConfig(parserConfig, caller, debugmode):
    '''
    Function to load configuration from the config files.
    Caller function is fcparser, fcdeparser or fclearning
    '''
    
    # Config dictionary which stores all the entries necessary for processing (the parameters
    # defined in general config. file and datasources config. files)
    config = {}
    paramError = False
    paramWarnings = 0
    
    # First get parameter dicts from parserConfig and show message error to user if exceptions
    # parserConfig_low will have lowercase keys to avoid possible differences with user notation
    parserConfig_low =  {k.lower(): v for k, v in parserConfig.items()}
    
    try:
        dataSources = parserConfig_low['datasources']
    except:
        print('\033[31m'+ "**CONFIG FILE ERROR** field: DataSources" +'\033[m')
        paramError = True
        
    
    if caller == 'fcparser':
        # Online parameter
        try:
            online = parserConfig_low['online']
            if not debugmode:
                if online is True:
                    print("* Online mode")
                elif online is False:
                    print("* Offline mode (multiprocess)")
        except:
            paramError = True
            print('\033[31m'+ "**CONFIG FILE ERROR** field: Online" +'\033[m')
            
            
        # Parsing output directory
        try:
            output = parserConfig_low['parsing_output']
        except:
            paramWarnings += 1
            if not debugmode:
                print('\033[33m'+ "**CONFIG FILE WARNING** missing field: Parsing_Output" +'\033[m')
            
        
        # Incremental_Output parameter
        try:
            config['Incremental'] = parserConfig_low['incremental_output']
            if not debugmode:
                print("* Incremental_output: "+str(config['Incremental']))
        except:
            paramWarnings += 1
            config['Incremental'] = False
            if not debugmode:
                print('\033[33m'+ "**CONFIG FILE WARNING** missing field: Incremental_Output")
                print(" * Setting default value: %s" %(config['Incremental']) +'\033[m')
                  
    
    if caller == 'fcdeparser':
        try:
            output = parserConfig_low['deparsing_output']
        except:
            print('\033[31m'+ "**CONFIG FILE ERROR** field: Deparsing_Output" +'\033[m')
            paramError = True
            
        try:
            config['threshold'] = parserConfig_low['deparsing_output']['threshold']
            print("Threshold: "+str(config['threshold']))
        except:
            print('\033[31m'+ "**CONFIG FILE ERROR** field: threshold" +'\033[m')
            paramError = True
        
        
    if caller == 'fclearning':
        # Online parameter
        try:
            online = parserConfig_low['online']
        except:
            online = False
            
        try:
            output = parserConfig_low['learning_output']
        except:
            print('\033[31m'+ "**CONFIG FILE ERROR** field: Learning_Output" +'\033[m')
            paramError = True
            
        if 'lperc' in parserConfig_low:
            config['Lperc'] = float(parserConfig_low['lperc'])
            print("* Lperc: "+str(config['Lperc']))
        else:
            print('\033[33m'+ "**CONFIG FILE WARNING** missing field: Lperc")
            paramWarnings += 1
            config['Lperc'] = 0.01;
            print(" * Setting default value: Lperc=%s" %(config['Lperc']) +'\033[m')

        if 'endlperc' in parserConfig_low:
            config['EndLperc'] = float(parserConfig_low['endlperc'])
            print("* EndLperc: "+str(config['EndLperc']))
        else:
            print('\033[33m'+ "**CONFIG FILE WARNING** missing field: EndLperc")
            paramWarnings += 1
            config['EndLperc'] = 0.0001;
            print(" * Setting default value: EndLperc=%s" %(config['EndLperc']) +'\033[m')
            
            
    # Number of cores used by the program
    if caller == 'fcparser' or caller == 'fclearning': 
        try: 
            config['Cores'] = int(parserConfig_low['processes'])
            if not debugmode:
                print("* Cores: "+str(config['Cores']))
    
        except:
            paramWarnings += 1
            config['Cores'] = 8
            if not debugmode:
                print('\033[33m'+ "**CONFIG FILE WARNING** missing field: Processes")
                print(" * Setting default value: %d cores" %(config['Cores']) +'\033[m')
            
            
    # Chunk size parameter (only for offline mode)
    try:
        if online is False:
            try: 
                config['Csize'] = 1024 * 1024 * int(parserConfig_low['max_chunk'])
            except:
                paramWarnings+=1
                config['Csize'] = 1024 * 1024 * config['Cores'];
                if not debugmode:
                    print('\033[33m'+ "**CONFIG FILE WARNING** missing field: Max_chunk")
                    print(" * Setting default chunk size: 1 MB" +'\033[m') # To understand why default chunk size is 1MB, check calling of frag function in fcparser.process_multifile()
    except:
        pass   
        
    
    # Time split parameters   
    if caller == 'fcparser' or caller == 'fcdeparser':  
        try: 
            parserConfig_low['split'] =  {k.lower(): v for k, v in parserConfig_low['split'].items()}
            config['Time'] = parserConfig_low['split']['time']
            if not debugmode:
                if config['Time']['window'] <= 60:
                    print("* Time sampling window: %d minutes" %(config['Time']['window']))
                elif config['Time']['window'] <= 1440:
                    print("* Time sampling window: %dh %dmin" %(config['Time']['window']/60, config['Time']['window']%60))
                else:
                    print('\033[31m'+ "**CONFIG FILE ERROR** Time sampling window above day is not implemented" +'\033[m')
                    exit(1)
        except KeyError as key:
            if key.args[0] == 'split' and not debugmode: 
                print('\033[33m'+ "**CONFIG FILE WARNING** missing field: SPLIT" +'\033[m')
            elif key.args[0] == 'time' and not debugmode: 
                print('\033[33m'+ "**CONFIG FILE WARNING** missing field: Time in SPLIT field")
            paramWarnings+=1
            if key.args[0] == 'window' and not debugmode:
                config['Time']['window'] = 5
            else:
                config['Time'] = {'window':5}
                
            if not debugmode:
                print(" * Setting default sampling time window: %s min." %(config['Time']['window']) +'\033[m')
            
        try:
            if 'start' in config['Time']:
                config['Time']['start'] = datetime.strptime(str(config['Time']['start']), "%Y-%m-%d %H:%M:%S")
                print("* Start time: %s" %(config['Time']['start']))
            if 'end' in config['Time']:
                config['Time']['end'] = datetime.strptime(str(config['Time']['end']), "%Y-%m-%d %H:%M:%S")
                print("* End time: %s" %(config['Time']['end']))
        except ValueError as val_error:
            print('\033[31m'+ val_error.args[0] +'\033[m')
            paramError = True
            
            
    # Keys parameter
    try: 
        config['Keys'] = parserConfig_low['keys']

    except:
        config['Keys'] = []

    # 'All' parameter
    if 'All' in parserConfig:
        config['All'] = bool(parserConfig_low['all'])
    else:
        config['All'] = False;
             

    
    # Output directory
    try:
        config['OUTDIR'] = output['dir']
        if not config['OUTDIR'].endswith('/'):
            config['OUTDIR'] = config['OUTDIR'] + '/'
    except (KeyError, TypeError, UnboundLocalError):
        config['OUTDIR'] = 'OUTPUT/'
        print(" ** Defining default output directory: '%s'" %(config['OUTDIR']))
    except:
        pass

    if not debugmode:
        try:
            shutil.rmtree(config['OUTDIR']+'/')
        except:
            pass
    
        if not os.path.exists(config['OUTDIR']): # Output directory named OUTPUT is created if none is defined in config. file
            os.mkdir(config['OUTDIR'])
            print("** Creating output directory %s" %(config['OUTDIR']))

    # Stats file
    try:
        config['OUTSTATS'] = output['stats']
    except (KeyError, TypeError, UnboundLocalError):
        config['OUTSTATS'] = 'stats.log'
        print(" ** Defining default log file: '%s'" %(config['OUTSTATS']))
    except:
        pass
        
    # Weights file
    try:
        config['OUTW'] = output['weights']
    except (KeyError, TypeError, UnboundLocalError):
        config['OUTW'] = 'weights.dat'
        print(" ** Defining default weights file: '%s'" %(config['OUTW']))
    except:
        pass
        

    # Sources settings. Data source config. file parameters stored in config[SOURCES] 
    config['SOURCES'] = {}
    for source in dataSources:
        config['SOURCES'][source] = {}
        dataSources[source] =  {k.lower(): v for k, v in dataSources[source].items()}
        
        try:
            config['SOURCES'][source]['CONFILE'] = dataSources[source]['config']
            if not os.path.exists(config['SOURCES'][source]['CONFILE']):
                print('\033[31m'+ "**CONFIG FILE ERROR** Unable to find file: %s" %(dataSources[source]['config']) +'\033[m')
                paramError = True
        except:
            print('\033[31m'+ "**CONFIG FILE ERROR** missing field: 'config' in %s field" %(source) +'\033[m')
            paramError = True
            
        if caller == 'fcparser':
            try:
                config['SOURCES'][source]['FILES'] = glob.glob(dataSources[source]['parsing'])
                if not config['SOURCES'][source]['FILES']:
                    print('\033[31m'+ "**CONFIG FILE ERROR** Unable to find file: %s" %(dataSources[source]['parsing']) +'\033[m')
                    paramError = True
            except:
                print('\033[31m'+ "**CONFIG FILE ERROR** missing field: 'parsing' in '%s' field" %(source) +'\033[m')
                paramError = True
                
        if caller == 'fcdeparser':
            try:
                config['SOURCES'][source]['FILESDEP'] = glob.glob(dataSources[source]['deparsing'])
                if not config['SOURCES'][source]['FILESDEP']:
                    print('\033[31m'+ "**CONFIG FILE ERROR** Unable to find file: %s" %(dataSources[source]['deparsing']) +'\033[m')
                    paramError = True
            except:
                print('\033[31m'+ "**CONFIG FILE ERROR** missing field: 'deparsing' in '%s' field" %(source) +'\033[m')
                paramError = True
                
        if caller == 'fclearning': 
            try:
                config['SOURCES'][source]['FILESTRAIN'] = glob.glob(dataSources[source]['learning'])
                if not config['SOURCES'][source]['FILESTRAIN']:
                    print('\033[31m'+ "**CONFIG FILE ERROR** Unable to find file: %s" %(dataSources[source]['learning']) +'\033[m')
                    paramError = True
            except:
                print('\033[31m'+ "**CONFIG FILE ERROR** missing field: 'learning' in '%s' field" %(source) +'\033[m')
                paramError = True
                
        
    # Check everything is ok in general configuration file before loading datasources config. files
    if paramError is True:
        print('\033[31m'+ "PROGRAM EXECUTION ABORTED DUE TO CONFIG. FILE ERRORS" +'\033[m')
        exit(1)
    else:
        if not debugmode:
            if paramWarnings:
                print('\033[33m'+ "EXECUTING PROGRAM WITH %d WARNINGS" %(paramWarnings) +'\033[m')
            else:
                print('\033[32m'+ "GENERAL CONFIGURATION FILE... OK" +'\033[m')
            
            
    # Loading parameters from datasources config. files
    print("LOADING DATA SOURCES CONFIGURATION FILES...")
    for source in dataSources:
        try:
            config['SOURCES'][source]['CONFIG'] = getConfiguration(dataSources[source]['config'])
        except:
            print('\033[31m'+ "Error while loading YAML file: %s'" %(dataSources[source]['config']) +'\033[m')
            print("Please, verify the file content fulfill the YAML format.")
            exit(1)
    
            
        
    config['FEATURES'] = {}
    config['STRUCTURED'] = {}
    config['RECORD_SEPARATOR'] = {}
    config['TIMEARG'] = {}
    config['TSFORMAT'] = {}

    # First, we check if all mandatory attributes are defined
    for source in config['SOURCES']:
        
        #config['SOURCES'][source]['CONFIG'] =  {k.lower(): v for k, v in config['SOURCES'][source]['CONFIG'].items()}
        try:
            config['STRUCTURED'][source] = config['SOURCES'][source]['CONFIG']['structured']
        except:
            paramError = True
            print('\n\033[31m'+ "** missing attribute: 'structured' in  %s data source'" %(source) +'\033[m')
        
        try:
            config['TSFORMAT'][source] = config['SOURCES'][source]['CONFIG']['timestamp_format']
        except:
            paramError = True
            print('\n\033[31m'+ "** missing attribute: 'timestamp_format' in  %s data source'" %(source) +'\033[m')
            
        try:
            config['TIMEARG'][source] = config['SOURCES'][source]['CONFIG']['timearg']
        except:
            print('\033[33m'+ "** missing attribute: 'timearg' in %s data source" %(source))
            print(" ** Assuming default variable labeled 'timestamp'" +'\033[m')
            config['TIMEARG'][source] = 'timestamp'
            
        # unstructured source
        if not config['STRUCTURED'][source]:
            try:
                config['RECORD_SEPARATOR'][source] = config['SOURCES'][source]['CONFIG']['separator'] 
            except:
                paramError = True
                print('\n\033[31m'+ "** missing attribute: 'separator' in %s data source'" %(source) +'\033[m')
        # structured source
        else:
            config['RECORD_SEPARATOR'][source] = config['SOURCES'][source]['CONFIG'].get('separator') or "\n"
        
        if paramError is True:
            print('\n\033[31m'+ "PROGRAM EXECUTION ABORTED DUE TO CONFIG. FILE ERRORS" +'\033[m')
            exit(1)
    
    
    # Now, variables and features are processed        
    for source in config['SOURCES']:  
        print("* File: %s" %(config['SOURCES'][source]['CONFILE']))
        
        config['FEATURES'][source] = config['SOURCES'][source]['CONFIG']['FEATURES']
        var_names = []
        
        for i in range(len(config['SOURCES'][source]['CONFIG']['VARIABLES'])):
            # Validate variable name
            if config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['name']:
                config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['name'] = str(config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['name'])
                var_names.append(config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['name'])
            else:
                paramError = True
                print('\033[31m'+ "** ConfigError - VARIABLES: empty name/id in variable %d" %(i) +'\033[m')

        for i in range(len(config['SOURCES'][source]['CONFIG']['FEATURES'])):
            # Validate feature name
            if config['SOURCES'][source]['CONFIG']['FEATURES'][i]['name']:
                config['SOURCES'][source]['CONFIG']['FEATURES'][i]['name'] = str(config['SOURCES'][source]['CONFIG']['FEATURES'][i]['name'])
            else:
                paramError = True
                print('\033[31m'+ "** ConfigError - FEATURES: missing name in feature %d" %(i) +'\033[m')

            # Validate variable field in feature
            if not 'variable' in config['SOURCES'][source]['CONFIG']['FEATURES'][i]:
                print('\033[31m'+ "** ConfigError - FEATURES: missing variable field in feature '%s'" %(config['SOURCES'][source]['CONFIG']['FEATURES'][i]['name']) +'\033[m')
                paramError = True
                config['SOURCES'][source]['CONFIG']['FEATURES'][i]['variable'] = None
            elif not config['SOURCES'][source]['CONFIG']['FEATURES'][i]['variable'] in var_names:
                print('\033[31m' + "Feature with name '%s' is defined using '%s'variable but this variable has not been defined previously" %(config['SOURCES'][source]['CONFIG']['FEATURES'][i]['name'], config['SOURCES'][source]['CONFIG']['FEATURES'][i]['variable']) +'\033[m')
                paramError = True
                config['SOURCES'][source]['CONFIG']['FEATURES'][i]['variable'] = None
        
        if paramError:
            print("Some errors in features or variables have been detected. Program execution is interrupted.")
            exit(1)


        # If source is not structured
        if not config['STRUCTURED'][source]:

            for i in range(len(config['SOURCES'][source]['CONFIG']['VARIABLES'])):
                config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['r_Comp'] = re.compile(config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['where'])

            for i in range(len(config['SOURCES'][source]['CONFIG']['FEATURES'])):
                    if config['SOURCES'][source]['CONFIG']['FEATURES'][i]['matchtype'] == 'regexp':
                        config['SOURCES'][source]['CONFIG']['FEATURES'][i]['r_Comp'] = re.compile(config['SOURCES'][source]['CONFIG']['FEATURES'][i]['value']+'$')

        else:
            # TODO: Retrieve from yaml
            #config['RECORD_SEPARATOR'][source] = config['SOURCES'][source]['CONFIG'].get('record_separator') or "\n"
            #print(config['RECORD_SEPARATOR'])
            for i in range(len(config['SOURCES'][source]['CONFIG']['FEATURES'])):
                    if config['SOURCES'][source]['CONFIG']['FEATURES'][i]['matchtype'] == 'regexp':
                        config['SOURCES'][source]['CONFIG']['FEATURES'][i]['r_Comp'] = re.compile(config['SOURCES'][source]['CONFIG']['FEATURES'][i]['value'])
    
    
        # Check if timestamp variable for each datasource is defined as matchtype=time to avoid future errors in parsing
        for source in config['SOURCES']: 
            timestamp_ok=0
            for i in range(len(config['SOURCES'][source]['CONFIG']['VARIABLES'])):
                if config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['name'] == config['TIMEARG'][source]:
                    timestamp_ok=1
                    if config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['matchtype'] == 'string':    
                        config['SOURCES'][source]['CONFIG']['VARIABLES'][i]['matchtype'] = 'time'
                        print('\033[33m'+ "Timestamp variable: '%s' from source: '%s' - matchtype is reassigned from 'string' to 'time'" %(config['TIMEARG'][source], source) +'\033[m')
                    break;
            if not timestamp_ok:
                print('\033[33m'+ "No timestamp variable has been found for '%s' data source" %(source) +'\033[m')                    
    
        
        # Preprocessing nfcapd files to obtain csv files.
        for source in dataSources:
            out_files = []
            for file in config['SOURCES'][source]['FILES']:
                if 'nfcapd' in file:
    
                    out_file = '/'.join(file.split('/')[:-1]) + '/temp_' + file.split('.')[-1] + ""
                    os.system("nfdump -r " + file + " -o csv >>"+out_file)
                    os.system('tail -n +2 '+out_file + '>>' + out_file.replace('temp',source))
                    os.system('head -n -3 ' + out_file.replace('temp',source) + ' >> ' + out_file.replace('temp',source) + '.csv')
                    out_files.append(out_file.replace('temp',source) + '.csv')
                    os.remove(out_file)
                    os.remove(out_file.replace('temp',source))
                    config['SOURCES'][source]['FILES'] = out_files
                    #delete_nfcsv = out_files
    
    
        # Process weight and made a list of features
        config['features'] = []
        config['weights'] = []
    
        for source in config['FEATURES']:
            # Create weight file
    
            for feat in config['SOURCES'][source]['CONFIG']['FEATURES']:
                try:    
                    config['features'].append(feat['name'])
                except Exception as e:
                    print("FEATURES: missing config key (%s)" %(e.message))
                    exit(1)    

                try:    
                    fw = feat['weight']
                    for var in config['SOURCES'][source]['CONFIG']['VARIABLES']:
                        if var['name'] == feat['variable']:
                            try:
                                fw2 = var['weight']
                            except:
                                fw2 = 1

                            fw = fw*fw2
                except:
                    fw = 1

                config['weights'].append(str(fw))



    return config



def debugProgram(caller, args):
    '''
    Function to debug program in order to obtain more information about execution process.
    Caller function is fcparser, fcdeparser or fclearning.
    Exec_point is related to the moment when we want to debug
    Args is the required data to print according to the exec point.
    '''
    
    if caller == 'fcparser.init_message':
        print('\033[33m'+ "Initializing debug mode...")
        print("-----------------------------------------------------------------------\n")
        print("\t\t\t DEBUGGING MODE")
        print("\n-----------------------------------------------------------------------")
        print("Press ENTER to process the next log entry")
        print("Enter \"go N\" to show the entry log number N, e.g.: go 78")
        print("Enter \"search string\" to show the next entry log matching that string, e.g.: search 12:45:01")
        print("Enter q for exit"+'\033[m')
        
        # Global regular expressions for matching user input
        global regex_goline; regex_goline=re.compile("go [0-9]+")
        global regex_searchstring; regex_searchstring=re.compile("search .+")
        
        return
    
    
    if 'fcparser' in caller:
        
        # Print data source
        if 'process_file.source' in caller:
            source = args[0]
            Nlogs = args[1]
            print("\n** Source: %s - %d entry logs **" %(source, Nlogs))
            return
        
        # Read user input
        if caller=='fcparser.user_input':
            actual_line = args[0]
            option = input("$ ")                     #option = ''    # go through the whole file                
            if option == 'q' or option == 'Q':
                exit(1)
            elif regex_goline.match(option):
                goline = int(regex_goline.search(option)[0][3:])
                return goline
            elif regex_searchstring.match(option):
                searchstring = regex_searchstring.search(option)[0][7:]
                return searchstring
            elif not option:
                return actual_line
            else:
                print('\033[31m'+ "Invalid option" +'\033[m')
                return 0
                
        # Print entry log
        if 'process_file.line' in caller:
            nEntry = args[0]
            log = args[1]
            print("\nEntry Log %d:\n%s" %(nEntry, log))
            return
        
        # Print record
        if 'process_log.record' in caller:
            record = args[0]
            #stdin.read(1)
            print("\nRecord with format 'variable_name': log_data\n%s" %(str(record)))
            
            none_variables = []
            none_value_variables = []
            for variable in record.variables:                    
                for i in range(len(record.variables[variable])):    # There might be more than one item in a variable (unstructured data)  
                    if record.variables[variable][i] is None:
                        none_variables.append(variable)                     # Invalid object (var=None)
                    elif hasattr(record.variables[variable][i], 'value'):
                        if record.variables[variable][i].value is None:     # Valid object but error while formatting value (var.value=None)
                            none_value_variables.append(variable)
            if none_variables:
                print('\033[33m'+ "Detected some None variables: %s" %(none_variables) +'\033[m')
            if none_value_variables:
                print('\033[33m'+ "Detected some None values in variables: %s" %(none_value_variables) +'\033[m')
            if not none_variables and not none_value_variables:
                print('\033[32m'+ "No invalid values detected"  +'\033[m')
                
            #if none_variables or none_value_variables: stdin.read(1)
            
                
        if 'process_log.observation' in caller:
            observation = args[0].data
            print("\nObservation vector: %s" %(str(observation)))
            
            features_counter = {}
            for obs in observation:
                if obs.value:
                    features_counter[obs.fName] = obs.value
                    
            print("Features with counter>0: %s\n" %(features_counter))
            
            #if 'daddr_private' not in features_counter and 'daddr_public' not in features_counter: stdin.read(1)
              
            
        
        
        
        
        
        
        
        
        
