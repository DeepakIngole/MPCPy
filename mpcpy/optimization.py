# -*- coding: utf-8 -*-
"""
``Optimization`` objects setup and solve mpc control optimization problems.  
The optimization uses ``models`` objects to  setup and solve the specified 
optimization problem type with the specified optimization package type.  
Constraint informaiton can be added to the optimization problem through the 
use of the constraint ``exodata`` object. Please see the ``exodata`` 
documentation for more information.

Classes
=======

.. autoclass:: mpcpy.optimization.Optimization
    :members: optimize, set_problem_type, set_package_type, 
              get_optimization_options, set_optimization_options, 
              get_optimization_statistics, 

Problem Types
=============

.. autoclass:: mpcpy.optimization.EnergyMin

.. autoclass:: mpcpy.optimization.EnergyCostMin

Package Types
=============

.. autoclass:: mpcpy.optimization.JModelica

"""

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from mpcpy import utility
from mpcpy import variables
from mpcpy import units
from pymodelica import compile_fmu
from pyjmi import transfer_optimization_problem;
from pyjmi.optimization.casadi_collocation import ExternalData
from scipy import optimize
import nlopt

#%% Optimization Class
class Optimization(object):
    '''Class for representing an optimization problem.    
 
    Parameters
    ----------
    Model :  mpcpy.model object
        Model with which to perform the optimization.
    problem_type : mpcpy.optimization.problem_type
        The type of poptimization problem to solve.  See specific documentation
        on available problem types.
    package_type : mpcpy.optimization.package_type
        The software package used to solve the optimization problem.  The model
        is translated into an optimization problem accoding to the problem_type
        to be solved in the specified package_type.  See specific documentation
        on available package types.
    objective_variable : string
        The name of the model variable to be used in the objective function.
    constraint_data : dictionary, optional
        ``exodata`` constraint object data attribute. 
    
    
    Attributes
    ----------
    Model :  mpcpy.model object
        Model with which to perform the optimization.
    objective_variable : string
        The name of the model variable to be used in the objective function.
    constraint_data : dictionary
        ``exodata`` constraint object data attribute. 
       
    '''
        
    def __init__(self, Model, problem_type, package_type, objective_variable, **kwargs):    
        '''Constructor of an optimization problem object.
        
        '''

        self.Model = Model;
        if 'constraint_data' in kwargs:
            self.constraint_data = kwargs['constraint_data'];
        else:
            self.constraint_data = {};
        self.objective_variable = objective_variable;
        self._problem_type = problem_type();
        self._package_type = package_type(self);
        
        if 'opt_package' in kwargs:
            self.solver_package = kwargs['opt_package'];
        else:
           pass
       
        if 'algorithm' in kwargs:
            self.algorithm = kwargs['algorithm'];
        else:
           pass 
        
        
    def optimize(self, start_time, final_time, **kwargs):
        '''Solve the optimization problem over the specified time horizon.
        
        Parameters
        ----------
        start_time : string
            Start time of estimation period.
        final_time : string
            Final time of estimation period.
            
        Yields
        ------
        Upon solving the optimization problem, this method updates the
        ``Model.control_data`` dictionary with the optimal control 
        timeseries for each control variable and the Model.measurements 
        dictionary with the optimal measurements under the ``'Simulated'`` key.
        
        '''

        self.Model._set_time_interval(start_time, final_time);
        self._problem_type._optimize(self, **kwargs);

    def set_problem_type(self, problem_type):
        '''Set the problem type of the optimization.
        
        Note that optimization options will be reset.
        
        Parameters
        ----------
        problem_type : mpcpy.optimization.problem_type
            New problem type to solve.  See specific documentation
            on available problem types.   
        
        '''

        self._problem_type = problem_type();
        package_type = type(self._package_type);
        self._package_type = package_type(self);

    def set_package_type(self, package_type):
        '''Set the solver package type of the optimization.

        Parameters
        ----------
        package_type : mpcpy.optimization.package_type
            New software package type to use to solve the optimization problem.
            See specific documentation on available package types.
            
        '''

        self._package_type = package_type(self);
        
    def get_optimization_options(self):
        '''Get the options for the optimization solver package.
        
        Returns
        -------
        opt_options : dictionary
            The options for the optimization solver package.  See specific 
            documentation on solver package for more information.
        
        '''
        
        return self._package_type._get_optimization_options();
        
    def set_optimization_options(self, opt_options):
        '''Set the options for the optimization solver package.
        
        Parameters
        ----------
        opt_options : dictionary
            The options for the optimization solver package.  See specific 
            documentation on solver package for more information.
        
        '''
        
        return self._package_type._set_optimization_options(opt_options);
        
    def get_optimization_statistics(self):
        '''Get the optimization result statistics from the solver package.
        
        Returns
        -------
        opt_statistics : dictionary
            The options for the optimization solver package.  See specific 
            documentation on solver package for more information.
        
        '''
        opt_statistics = self._package_type._get_optimization_statistics();
        return opt_statistics;
        
#%% Problem Type Abstract Interface
class _Problem(object):
    '''Interface for a problem type.
    
    '''

    __metaclass__ = ABCMeta;
    
    def __init__(self):
        '''Constructor of a problem type object.
        
        ''' 

        pass;
        
    @abstractmethod
    def _optimize():
        '''Optimization-problem specific call to solve the problem.
        
        Parameters
        ----------
        Optimization : mpcpy.optimization.Optimization object
            The optimization object containing the Model and solver package
            attributes.
        
        ''' 
        
        pass;    
        
    @abstractmethod
    def _setup_jmodelica():
        '''Setup the problem with JModelica.

        Parameters
        ----------
        JModelica : mpcpy.optimization.JModelica object
            The JModelica solver package object.
        Optimization : mpcpy.optimization.Optimization object
            The optimization object containing the Model and solver package
            attributes.
        
        ''' 
        
        pass;
        
#%% Solver Type Abstract Interface
class _Package(object):
    '''Interface for a solver package type.
    
    '''
    
    __metaclass__ = ABCMeta;
    
    @abstractmethod
    def _energymin(self):
        '''Optimization package-specific call to minimize the integral of the 
        objective variable over the time horizon.
        
        Yields
        ------
        Upon solving the optimization problem, this method updates the
        ``Optimization.Model.control_data`` dictionary with the optimal control 
        timeseries for each control variable and the 
        Optimization.Model.measurements dictionary with the optimal 
        measurements under the ``'Simulated'`` key.
        
        '''
    
        pass;
        
    @abstractmethod
    def _energycostmin(self):
        '''Optimization package-specific call to minimize the integral of the 
        objective variable times a time-varying weight over the time horizon.
        
        Yields
        ------
        Upon solving the optimization problem, this method updates the
        ``Optimization.Model.control_data`` dictionary with the optimal control 
        timeseries for each control variable and the 
        Optimization.Model.measurements dictionary with the optimal 
        measurements under the ``'Simulated'`` key.
        
        '''
        
        pass;
        
    @abstractmethod
    def _parameterestimate(self):
        '''Optimization package-specific call to minimize the error between 
        simulated and measured data by tuning model parameters.
        
        Yields
        ------
        Upon solving the optimization problem, this method updates the
        ``Optimization.Model.parameter_data`` dictionary ``'Value`'' key
        for each parameter with the estimated value.
        
        '''
        
        pass;
        
    @abstractmethod
    def _get_optimization_options(self):
        '''Get the optimization options of the solver package in a dictionary.
        
        '''
        
        pass;   
        
    @abstractmethod
    def _set_optimization_options(self):
        '''Set the optimization options of the solver package from a dictionary.
        
        '''
        
        pass;
        
    @abstractmethod
    def _get_optimization_statistics(self):
        '''Get the optimization result statistics from the solver package.
        
        '''
        
        pass;    
              
#%% Problem Type Implementation
class EnergyMin(_Problem):
    '''Minimize the integral of the objective variable over the time 
    horizon.
    
    '''

    def _optimize(self, Optimization, **kwargs):
        '''Solve the energy minimization problem.
        
        '''
        
        Optimization._package_type._energymin(Optimization);
        
    def _setup_jmodelica(self, JModelica, Optimization):
        '''Setup the optimization problem for JModelica.
        
        '''
        
        JModelica.Model = Optimization.Model;
        JModelica.objective = 'mpc_model.' + Optimization.objective_variable;
        JModelica.extra_inputs = {};
        JModelica._initalize_mop();
        JModelica._write_control_mop(Optimization);
        JModelica._compile_transfer_problem();
        
class EnergyCostMin(_Problem):
    '''Minimize the integral of the objective variable multiplied by a 
    time-varying weighting factor over the time horizon.
    
    '''

    def _optimize(self, Optimization, **kwargs):
        '''Solve the energy cost minimization problem.
        
        '''

        price_data = kwargs['price_data'];
        Optimization._package_type._energycostmin(Optimization, price_data);
        
    def _setup_jmodelica(self, JModelica, Optimization):
        '''Setup the optimization problem for JModelica.
        
        '''
        
        JModelica.Model = Optimization.Model;
        JModelica.objective = 'mpc_model.' + Optimization.objective_variable + '*pi_e';
        JModelica.extra_inputs = {};
        JModelica.extra_inputs['pi_e'] = [];
        JModelica._initalize_mop();
        JModelica._write_control_mop(Optimization);
        JModelica._compile_transfer_problem();
        
class _ParameterEstimate(_Problem):
    '''Minimize the error between simulated and measured data by adjusting 
    time-invariant parameters of the model.  
    
    To be called from mpcpy.models.JModelica only.
    
    '''

    def _optimize(self, Optimization, **kwargs):
        '''Solve the parameter estimation problem.
        
        '''
        
        Optimization._package_type._parameterestimate(Optimization, kwargs['measurement_variable_list']);
        
    def _setup_jmodelica(self, JModelica, Optimization):
        '''Setup the optimization problem for JModelica.
        
        '''
        
        JModelica.Model = Optimization.Model;
        JModelica.objective = '0';
        JModelica.extra_inputs = {};
        JModelica._initalize_mop();
        JModelica._write_parameter_estimate_mop();
        JModelica._compile_transfer_problem();
        
#%% Solver Type Implementation
class JModelica(_Package, utility._FMU):
    '''Use JModelica to solve the optimization problem.
    
    This package is compatible with ``models.Modelica`` objects.  Please
    consult the JModelica user guide for more information regarding 
    optimization options and solver statistics.
    
    '''
    
    def __init__(self, Optimization):
        '''Constructor of the JModelica solver package class.
        
        '''
        
        # Setup JModelica optimization problem
        Optimization._problem_type._setup_jmodelica(self, Optimization);
        # Set default optimization options
        self._set_optimization_options(self.opt_problem.optimize_options(), init = True)
    
    def _energymin(self, Optimization):
        '''Perform the energy minimization.
        
        '''
        
        self._simulate_initial(Optimization);
        self._solve();
        self._get_control_results(Optimization);           
        
    def _energycostmin(self, Optimization, price_data):
        '''Perform the energy cost minimization.
        
        '''
        
        self.other_inputs['pi_e'] = price_data['pi_e'];
        self._simulate_initial(Optimization);
        self._solve();   
        self._get_control_results(Optimization);                                      
        
    def _parameterestimate(self, Optimization, measurement_variable_list):
        '''Perform the parameter estimation.
        
        '''

        self.measurement_variable_list = measurement_variable_list;        
        self._simulate_initial(Optimization);
        self._solve();
        self._get_parameter_results(Optimization);
        
    def _initalize_mop(self):
        '''Start writing the mop file.
        
        '''

        # Open .mo
        mofile = open(self.Model.mopath,'r');
        # Initiate .mop
        self.moppath = self.Model.mopath+'p';        
        self.mopfile = open(self.moppath,'w');
        # Copy .mo
        for line in mofile:
            # Write line to file
            if 'end ' + self.Model.modelpath.split('.')[0] in line:
                break;
            elif 'within ;' not in line and 'annotation (uses' not in line and '(version="' not in line:
                self.mopfile.write(line);
        mofile.close();                
        # Add initialization model to package.mop (must be same name as model in optimization)
        
        self.mopfile.write('\n');
        self.mopfile.write('  model ' + self.Model.modelpath.split('.')[-1] + '_initialize\n');
        package = self.Model.modelpath.split('.')[1:];
        self.mopfile.write('    ' + '.'.join(package) + ' mpc_model(\n');
        # Add parameters if they exist
        if self.Model.parameter_data:
            for key in self.Model.parameter_data.keys()[:-1]:
                self.mopfile.write('     ' + key + '=' + str(self.Model.parameter_data[key]['Value'].get_base_data()) + ',\n');
            self.mopfile.write('     ' + self.Model.parameter_data.keys()[-1] + '=' + str(self.Model.parameter_data[self.Model.parameter_data.keys()[-1]]['Value'].get_base_data()) + ');\n');
        else:
            self.mopfile.write(');\n');
        # Instantiate optimization model inputs
        for key in self.Model.input_names:
            self.mopfile.write('    input Real ' + key + '= mpc_model.' + key + ';\n');
        # Add extra inputs required for optimization problem
        self._init_input_names = self.Model.input_names;  
        self.other_inputs = self.Model.other_inputs;
        for key in self.extra_inputs.keys():
            self._init_input_names.append(key);
            self.other_inputs[key] = self.extra_inputs[key];
            self.mopfile.write('    input Real ' + key+';\n');
        # Instantiate cost function
        self.mopfile.write('    Real J(start = 0, fixed=true);\n');
        # Define cost function
        self.mopfile.write('  equation\n');
        self.mopfile.write('    der(J) = '+self.objective+';\n');
        # End initalization model
        self.mopfile.write('  end ' + self.Model.modelpath.split('.')[-1] + '_initialize;\n');
        # Save the model path of the initialization and optimziation models
        self.mopmodelpath = self.Model.modelpath.split('.')[0] + '.' + self.Model.modelpath.split('.')[-1];
        
    def _write_control_mop(self, Optimization):
        '''Complete the mop file for a control optimization problem.
        
        '''

        self.mopfile.write('\n');
        self.mopfile.write('  optimization ' + self.Model.modelpath.split('.')[-1] + '_optimize (objective = (J(finalTime)), startTime=start_time, finalTime=final_time)\n');
        # Instantiate optimization model
        self.mopfile.write('    extends ' + self.Model.modelpath.split('.')[-1] + '_initialize;\n');
        # Add start time and final time parameter
        self.mopfile.write('    parameter Real start_time = 0;\n');
        self.mopfile.write('    parameter Real final_time = 86400;\n');
        # Remove control variables from input_names for optimization    
        self.opt_input_names = [];
        for key in self._init_input_names:
            if key not in self.Model.control_data.keys():
                self.opt_input_names.append(key);        
        # Instantiate constraint variables as inputs, add to input_names and other_inputs
        for key in Optimization.constraint_data.keys():
            for field in Optimization.constraint_data[key]:     
                if field != 'Cyclic' and field != 'Final' and field != 'Initial':
                    key_new = key.replace('.', '_') + '_' + field;
                    self.opt_input_names.append(key_new);
                    self.other_inputs[key_new] = Optimization.constraint_data[key][field];
                    self.mopfile.write('    input Real ' + key_new + ';\n');
        # Define constraint_data
        self.mopfile.write('  constraint\n');
        for key in Optimization.constraint_data.keys():
            for field in Optimization.constraint_data[key]:
                key_new = key.replace('.', '_') + '_' + field;                
                if field == 'GTE':
                    self.mopfile.write('    mpc_model.' + key + ' >= ' + key_new + ';\n');
                elif field == 'dGTE':
                    self.mopfile.write('    der(mpc_model.' + key + ') >= ' + key_new + ';\n');                    
                elif field == 'LTE':
                    self.mopfile.write('    mpc_model.' + key + ' <= ' + key_new + ';\n');
                elif field == 'dLTE':
                    self.mopfile.write('    der(mpc_model.' + key + ') <= ' + key_new + ';\n');                      
                elif field == 'Initial':
                    self.mopfile.write('    mpc_model.' + key + '(startTime)=' + str(Optimization.constraint_data[key][field].get_base_data()) + ';\n');
                elif field == 'Final':
                    self.mopfile.write('    mpc_model.' + key + '(finalTime)=' + str(Optimization.constraint_data[key][field].get_base_data()) + ';\n');
                elif field == 'Cyclic':
                    self.mopfile.write('    mpc_model.' + key + '(startTime)=mpc_model.' + key + '(finalTime);\n');                   
        # End optimization portion of package.mop
        self.mopfile.write('  end ' + self.Model.modelpath.split('.')[-1] + '_optimize;\n');
        # End package.mop and save
        self.mopfile.write('end ' + self.Model.modelpath.split('.')[0] + ';\n'); 
            
        # Close files
        self.mopfile.close();      
        
    def _write_parameter_estimate_mop(self):
        '''Complete the mop file for a parameter estimation problem.
        
        '''

        self.mopfile.write('\n');
        self.mopfile.write('optimization ' + self.Model.modelpath.split('.')[-1] + '_optimize (startTime=start_time, finalTime=final_time)\n');
        # Add start time and final time parameter
        self.mopfile.write('    parameter Real start_time = 0;\n');
        self.mopfile.write('    parameter Real final_time = 86400;\n');
        #  Instantiate MPC model with free parameters
        i = 1;
        free_parameters = [];
        for key in self.Model.parameter_data.keys():
            if self.Model.parameter_data[key]['Free'].get_base_data():
                free_parameters.append(key);
        I = len(free_parameters);
        for key in free_parameters:
            if i == 1:
                line = '    extends ' + self.Model.modelpath.split('.')[-1] + '_initialize (mpc_model.' + key + '(free=true, initialGuess='+str(self.Model.parameter_data[key]['Value'].get_base_data())+', min='+str(self.Model.parameter_data[key]['Minimum'].get_base_data())+', max='+str(self.Model.parameter_data[key]['Maximum'].get_base_data())+'),\n';
            elif i == I:
                line = '      mpc_model.' + key + '(free=true, initialGuess='+str(self.Model.parameter_data[key]['Value'].get_base_data())+', min='+str(self.Model.parameter_data[key]['Minimum'].get_base_data())+', max='+str(self.Model.parameter_data[key]['Maximum'].get_base_data())+'));\n';
            else:
                line = '      mpc_model.' + key + '(free=true, initialGuess='+str(self.Model.parameter_data[key]['Value'].get_base_data())+', min='+str(self.Model.parameter_data[key]['Minimum'].get_base_data())+', max='+str(self.Model.parameter_data[key]['Maximum'].get_base_data())+'),\n';
            self.mopfile.write(line);
            i = i + 1;    
        # End optimization portion of package.mop
        self.mopfile.write('end ' + self.Model.modelpath.split('.')[-1] + '_optimize;\n');
        # End package.mop and save    
        self.mopfile.write('end ' + self.Model.modelpath.split('.')[0] + ';\n');
        # Close files
        self.mopfile.close();
        
    def _simulate_initial(self, Optimization):
        '''Simulate the model for an initial guess of the optimization solution.
        
        '''

        # Set Exogenous
        self.weather_data = self.Model.weather_data;
        self.internal_data = self.Model.internal_data;
        self.control_data = self.Model.control_data;
        if type(Optimization._problem_type) is _ParameterEstimate:
            plt.figure(1)
            self.other_inputs = self.Model.other_inputs;
            self.opt_input_names = self._init_input_names;
            # Otherwise inputs set by write control mop
        # Set input_names
        self.input_names = self._init_input_names;
        # Set measurements
        self.measurements = {};
        for key in self.Model.measurements.keys():
            self.measurements['mpc_model.' + key] = self.Model.measurements[key];           
        # Set timing
        self.start_time_utc = self.Model.start_time_utc;
        self.final_time_utc = self.Model.final_time_utc;     
        self.elapsed_seconds = self.Model.elapsed_seconds;        
        # Simulate fmu
        self._simulate_fmu();
        # Store initial simulation
        self.res_init = self._res;
                                            
    def _solve(self):
        '''Solve the optimization problem.
        
        '''
        # Set start and final time
        self.Model.elapsed_seconds
        # Create input_mpcpy_ts_list
        self._create_input_mpcpy_ts_list_opt();
        # Set inputs
        self._create_input_object_from_input_mpcpy_ts_list(self._input_mpcpy_ts_list_opt);          
        # Create ExternalData structure
        self._create_external_data();
        # Set optimization options
        self.opt_options['external_data'] = self.external_data;
        self.opt_options['init_traj'] = self.res_init;
        self.opt_options['nominal_traj'] = self.res_init;
        self.opt_options['n_e'] = self._sim_opts['ncp'];
        # Set parameters if they exist
        if hasattr(self, 'parameter_data'):
            for key in self.parameter_data.keys():
                self.opt_problem.set(key, self.parameter_data[key]['Value'].get_base_data());
        # Set start and final time
        self.opt_problem.set('start_time', 0);
        self.opt_problem.set('final_time', self.Model.elapsed_seconds);
        # Optimize
        self.res_opt = self.opt_problem.optimize(options=self.opt_options);
        print(self.res_opt.get_solver_statistics());
        
    def _create_external_data(self):   
        '''Define external data inputs to optimization problem.
        
        '''

        quad_pen = OrderedDict();  
        N_mea = 0;
        if hasattr(self, 'measurement_variable_list'):
            for key in self.measurement_variable_list:
                df = self.Model.measurements[key]['Measured'].get_base_data()[self.Model.start_time:self.Model.final_time].to_frame();
                df_simtime = self._add_simtime_column(df);
                mea_traj = np.vstack((df_simtime['SimTime'].get_values(), \
                                     df_simtime[key].get_values()));
                quad_pen['mpc_model.' + key] = mea_traj;
                N_mea = N_mea + 1;
        else:
            Q = None;
        # Create objective error weights
        Q = np.diag(np.ones(N_mea));
        # Eliminate inputs from optimization problem 
        eliminated = {};
        i = 1;
        N_input = 0;
        if self._input_object:
            for key in self._input_object[0]:
                input_traj = np.vstack((np.transpose(self._input_object[1][:,0]), \
                                       np.transpose(self._input_object[1][:,i])));
                eliminated[key] = input_traj; 
                N_input = N_input + 1;
                i = i + 1;           
        # Create ExternalData structure
        self.external_data = ExternalData(Q=Q, quad_pen=quad_pen, eliminated=eliminated);
        
    def _get_control_results(self, Optimization):
        '''Update the control data dictionary in the model with optimization results.
        
        '''

        fmu_variable_units = self._get_fmu_variable_units();                                     
        for key in self.Model.control_data.keys():
            data = self.res_opt['mpc_model.' + key];
            time = self.res_opt['time'];
            timedelta = pd.to_timedelta(time, 's');
            timeindex = self.start_time_utc + timedelta;
            ts = pd.Series(data = data, index = timeindex);
            ts.name = key;
            unit = self._get_unit_class_from_fmu_variable_units('mpc_model.' + key,fmu_variable_units);
            if not unit:
                unit = units.unit1;                
            Optimization.Model.control_data[key] = variables.Timeseries(key, ts, unit);  
        for key in Optimization.Model.measurements.keys():
            data = self.res_opt['mpc_model.' + key];
            time = self.res_opt['time'];
            timedelta = pd.to_timedelta(time, 's');
            timeindex = self.start_time_utc + timedelta;
            ts = pd.Series(data = data, index = timeindex);
            ts.name = key;
            unit = self._get_unit_class_from_fmu_variable_units('mpc_model.' + key,fmu_variable_units);
            if not unit:
                unit = units.unit1;                
            Optimization.Model.measurements[key]['Simulated'] = variables.Timeseries(key, ts, unit);
            
    def _get_parameter_results(self, Optimization):
        '''Update the parameter data dictionary in the model with optimization results.
        
        '''

        for key in Optimization.Model.parameter_data.keys():
            if Optimization.Model.parameter_data[key]['Free'].get_base_data():
                self.fmu_variable_units = self._get_fmu_variable_units();
                unit = self._get_unit_class_from_fmu_variable_units('mpc_model.'+key, self.fmu_variable_units);
                if not unit:
                    unit = units.unit1;
                data = self.res_opt.initial('mpc_model.' + key);
                Optimization.Model.parameter_data[key]['Value'].set_display_unit(unit);
                Optimization.Model.parameter_data[key]['Value'].set_data(data);        
        
    def _compile_transfer_problem(self):
        '''Compile the initialization model and transfer the optimziation problem.
        
        '''
        
        # Compile the optimization initializaiton model                                             
        self.fmupath = compile_fmu(self.mopmodelpath + '_initialize', \
                                   self.moppath, \
                                   compiler_options = {'extra_lib_dirs':self.Model.libraries});
        kwargs = {};
        kwargs['fmupath'] = self.fmupath;
        self._create_fmu(kwargs);
        # Transfer optimization problem to casADi                         
        self.opt_problem = transfer_optimization_problem(self.mopmodelpath + '_optimize', \
                                                         self.moppath, \
                                                         compiler_options = {'extra_lib_dirs':self.Model.libraries});
                                                         
    def _get_optimization_options(self):
        '''Get the JModelica optimization options in a dictionary.
        
        '''
        
        return self.opt_options;
        
    def _set_optimization_options(self, opt_options, init = False):
        '''Set the JModelica optimization options using a dictionary.
        
        '''
        # Check that automatically set options are not being changed
        if not init:
            for key in opt_options:
                if key in ['external_data', 'init_traj', 'nominal_traj', 'n_e']:
                    if opt_options[key] != self.opt_options[key]:
                        raise KeyError('Key {} is set automatically upon solve.'.format(key));
        # Set options
        self.opt_options = opt_options;
        
    def _get_optimization_statistics(self):
        '''Get the JModelica optimization result statistics.
        
        '''
        
        return self.res_opt.get_solver_statistics();
    
class Python(_Package, utility._FMU):
    '''Python interface for NLOpt, scipy and JModelica.org Nelder-Mead
    Please  the  user guides for more information regarding 
    optimization options and solver statistics.
    
    '''
    
    
    def __init__(self, Optimization):
        '''Constructor of the JModelica solver package class.
        
        '''
        
        #where to put keywords for (i) package (NLOpt) and (ii) method (nm)
        
        # Setup JModelica optimization problem
        Optimization._problem_type._setup_jmodelica(self, Optimization);
        # Set default optimization options
        self._set_optimization_options(self.opt_problem.optimize_options(), init = True)
    
    def _energymin(self, Optimization):
        '''Perform the energy minimization.
        
        '''
        self._simulate_initial(Optimization);
        self._solve();
        self._get_control_results(Optimization);           
        
    def _energycostmin(self, Optimization, price_data):
        pass
    
    def _parameterestimate(self, Optimization, measurement_variable_list):
        pass
        
    def _get_optimization_options(self):
        '''Get the JModelica optimization options in a dictionary.
        
        '''
        
        return self.opt_options;
        
    def _set_optimization_options(self, opt_options, init = False):
        '''Set the JModelica optimization options using a dictionary.
        
        '''
        # Check that automatically set options are not being changed
        if not init:
            for key in opt_options:
                if key in ['external_data', 'init_traj', 'nominal_traj', 'n_e']:
                    if opt_options[key] != self.opt_options[key]:
                        raise KeyError('Key {} is set automatically upon solve.'.format(key));
        # Set options
        self.opt_options = opt_options;
        
    def _get_optimization_statistics(self):
        '''Get the JModelica optimization result statistics.
        
        '''
        
        return self.res_opt.get_solver_statistics();

    def _solve(self):
        '''Solve the optimization problem.
        
        '''
        # Set start and final time
        self.Model.elapsed_seconds
        # Create input_mpcpy_ts_list
        self._create_input_mpcpy_ts_list_opt();
        # Set inputs
        self._create_input_object_from_input_mpcpy_ts_list(self._input_mpcpy_ts_list_opt);          
        # Create ExternalData structure
        self._create_external_data();
        # Set optimization options
        self.opt_options['external_data'] = self.external_data;
        self.opt_options['init_traj'] = self.res_init;
        self.opt_options['nominal_traj'] = self.res_init;
        self.opt_options['n_e'] = self._sim_opts['ncp'];
        # Set parameters if they exist
        if hasattr(self, 'parameter_data'):
            for key in self.parameter_data.keys():
                self.opt_problem.set(key, self.parameter_data[key]['Value'].get_base_data());
        # Set start and final time
        self.opt_problem.set('start_time', 0);
        self.opt_problem.set('final_time', self.Model.elapsed_seconds);
        # Optimize
        self.res_opt = self.opt_problem.optimize(options=self.opt_options);
        print(self.res_opt.get_solver_statistics());
        


#################################################################################
    
    def wrapper_sim_opt(self, **kwargs):
        

        # get updated x_init
        if 'x_init' in kwargs:
            x = kwargs['x_init']
        else:
            print 'error'

        if 'x_list' in kwargs:
            x_list = kwargs['x_list']
        else:
            print 'error'
          
        # get updated mue
        if 'mue' in kwargs:
            mue = kwargs['mue']
        else:
            print 'error'
            
        # how many opt variables = size of input x array
        opt_disc = x.size       
        
        #lower and upper bounds for optimization variables
        lower =[]
        upper =[]
        initial = []
        final = []
        cyclic = []
        for key in Optimization.constraint_data.keys():
            # Dave check Synthax: Check if key is in contro..i dont want bounds of state variables
            if key in Optimization.Model.control_data:
                for field in Optimization.constraint_data[key]:
                    if field == 'GTE':
                       # Dave check synthax - this are always static variables
                        lw = Optimization.constraint_data[key][field].get_base_data()
                        lower.append(lw)
                    else:
                        lower.append(None)  
                   
                    if field == 'LTE':
                        # Dave check synthax - this are always static variables
                        up = Optimization.constraint_data[key][field].get_base_data()
                        upper.append(up)
                    else:
                        upper.append(None)                
                    
                    if field == 'Initial':
                        # Dave check synthax - this are always static variables
                        ini = Optimization.constraint_data[key][field].get_base_data()
                        initial.append(ini)
                    else:
                        initial.append(None)                                  
                    
                    if field == 'Final':
                        # Dave check synthax - this are always static variables
                        fi = Optimization.constraint_data[key][field].get_base_data()
                        final.append(fi)
                    else:
                        final.append(None) 
                       
                    if field == 'Cyclic':
                        # Dave check synthax - this are always static variables
                        cyc = Optimization.constraint_data[key][field].get_base_data()
                        cyclic.append(cyc)
                    else:
                        cyclic.append(None) 
            else:
                    pass
                   
        # upper and lower bound          
        bnds_list = zip(upper,lower)

        # convert it into touple
        bnds = tuple(bnds_list)          
 
        
        #total number of opt variables
        nr_opt_variables = np.sum(opt_disc)
        
        # get solver parameter (update for each package)
        solver_parameter = self.opt_options
        
        
        # check which package and which algorithm
        if Optimization.solver_package == 'nlopt':
            
            if Optimization.algorithm == 'CRS2_LM':
                opt = nlopt.opt(nlopt.GN_CRS2_LM, nr_opt_variables)
            
            if Optimization.algorithm == 'ESCH':
                opt = nlopt.opt(nlopt.GN_ESCH, nr_opt_variables)
                
            if Optimization.algorithm == 'DIRECT_L':
                opt = nlopt.opt(nlopt.GN_DIRECT_L, nr_opt_variables)
                 
            if Optimization.algorithm == 'NEWUOA_BOUND':
                opt = nlopt.opt(nlopt.LN_NEWUOA_BOUND, nr_opt_variables)
            
            if Optimization.algorithm == 'NELDERMEAD':
                opt = nlopt.opt(nlopt.LN_NELDERMEAD, nr_opt_variables)
            
            opt.set_min_objective(run_sim_opt)
            
            # check additional solver settings
            if 'xtol_rel' in solver_parameter:
                opt.set_xtol_rel(solver_parameter['xtol_rel'])
            else:
                pass
            #add addiontonal mix, max iter, func eval...
            
            try: 
                lower = [i[0] for i in bnds]
                upper = [i[1] for i in bnds]
                
                opt.set_lower_bounds(lower)
                opt.set_upper_bounds(upper)
            except:
                print 'no bounds defined'
                
 
            #perform optimization    
            xopt = opt.optimize(x)
            f_opt = opt.last_optimum_value()
         
        # Fix..neds to be updated    
        if Optimization.solver_packag == 'scipy':   
            
            if Optimization.algorithm == 'TNC':
                xopt = optimize.minimize(run_sim_opt, x, method='TNC', bounds=bnds, args=args)
    
        if Optimization.solver_packag == 'JModelica':   
            
            if Optimization.algorithm == 'NELDERMEAD':
                try: 
                    lower = [i[0] for i in bnds]
                    upper = [i[1] for i in bnds]
    
                except:
                    print 'no bounds defined'
                
                x_opt,f_opt,nbr_iters,nbr_fevals,solve_time = dfo.fmin("sim_based_cost.py",
                xstart=x0,lb=lower,ub=upper,alg=1,nbr_cores=4,x_tol=10,f_tol=10,max_iters=200,plot_conv=True, plot=True)
                xopt = [x_opt,f_opt,nbr_iters,nbr_fevals,solve_time]
        return xopt
    
        def cost_function(sim_res, x, mue):
            """
            Computate cost function
            sim_res = .fmu result simulation file
            x = input (not sure if needed)
            mue = penalty multiplier
            (1) extract simulation results
            (2) Computate cost function
            (3) return cost function
    
            """
            # variables needed
            #Dave change for not Modelica based FMI?
            t_sim = sim_res['time']
            
            #optimization variables (energy)
            J = sim_res[optimization.objective_variable]
            
            #constraint violations
            
            #how to access names of constraints? where to specifiy
            # where to specify min, max values.. in model or in framework?
            # Dave constraint violation - tricky to generalize
            
            # get state constraints:
            error_lower =[]
            error_upper = []
            
            for key in Optimization.constraint_data.keys():
                # check just state constraints
                if key not in Optimization.Model.control_data:
                    # here we (can) have constraint trajectories
                    for field in Optimization.constraint_data[key]:
                        
                        # Dave: check Synthax + make sure that time stamps are equal    
                        if field == 'GTE':
                            lw = Optimization.constraint_data[key][field].get_base_data()
                            error_l = np.trapz(np.maximum(0,sim_res[key]- lw), t_sim)
                            error_lower.append(error_l)
                        else:
                            pass  
                       
                        if field == 'LTE':
                            up = Optimization.constraint_data[key][field].get_base_data()
                            error_u = np.trapz(np.maximum(0, up - sim_res[key]), t_sim)
                            error_upper.append(error_u)
                        else:
                            pass

  
            # Compute error 
            # distinguish between constant bounds and trajectory bounds
            # if equal constraints (init and end temp) add power term
            
            # Dave: tricky to generalze: there could be point constraints (init temp) and path constraints
            # compute total error based on lower and upper violations
            total_error = sum(error_lower) + sum(error_upper)
            
            #compute cost function
            cost = J + mue * (total_error)
            
            return cost
    
    
    
        def update_input(x, x_list, key):
            indices = []
            # check indices of variables
            for i, item in enumerate(x[1]):
                if key in item:
                    indices.append(i)    
    
 
            # create new mpcpy variable
            mpcpy_var = Optimization.Model.control_data[key]
            
            # make sure that units fit
            mpcpy_var.set_display_unit(mpcpy_var.get_base_unit())
            
            # control variable update based on inupt x[0] and indices
            control_update = x[0][indices]
            
            #create pandas time series
            ts = pd.Series(index = mpcpy_var.get_base_data().index, data = control_update)
            mpcpy_var.set_data(ts)
            
            # finally, set updated control variable
            Optimization.Model.control_data[key] = mpcpy_var    
    
    
    
        def run_sim_opt(x):
            """
            Solve the optimization 
            (1) definie inputs
            (2) Run the simulation
            (3) compute the cost function
            (4) return the value of the cost function 
            """
            # input trajectories
            #fix: hard coded final an starttime
            #fix: if different length of input 
            #update contro ldata object with new inputs overwriting data dict
            input_list = []
            
            for key in Optimization.Model.control_data.keys():
                # call function update_inpute() to update control inputs
                update_input(x=x, x_list=x_list, key=key)
                
                # create input list based on names
                input_list.append(Optimization.Model.control_data[key])

            #create input_object
            self._create_input_object_from_input_mpcpy_ts_list(input_list);
            
            # Dave: would like to create a fmu object here: sim_res = ... possible?
            self._res = simulate_model.simulate(start_time = 0, \
                                           final_time = self.elapsed_seconds, \
                                           input = self._input_object, \
                                           options = self._sim_opts);
        

            # compute the value of the cost function
            cost = cost_function(sim_res, x, mue)
            
            return cost
    
    
    def penalty_opt(self, muefun):
        
        # get x_init and penalty multiplier mue: first iteration get global, \
        # then update per iteration
        
        # Dave: x = discretized opt. variables: e.g.: T_s = [300,300,300,300...]
        # For first tests - discretize based on pandas time steps
        xx = []
        xx_inf =[]
        # second idea: two lists
        for key in Optimization.Model.control_data.keys():
            var_pandas = Optimization.Model.control_data[key].get_base_data()
            var = var_pandas.values
            #list with size of control variales.. every entry = np.array
            xx.append(var)
            # add var.size times the name of the variable to the list
            xx_inf.extend([key]*var.size)
            
        # original
        input_list = [];
        for key in Optimization.Model.control_data.keys():
            var_pandas = Optimization.Model.control_data[key].get_base_data()
            var = var_pandas.values
            #list with size of control variales.. every entry = np.array
            xx.append(var)
            input_list.append(Optimization.Model.control_data[key])
          
            
        #third idea = enumerate also same variable (temp1, temp2, temp3)            
            
        for key in Optimization.Model.control_data.keys():
            var_pandas = Optimization.Model.control_data[key].get_base_data()
            var = var_pandas.values
            for i, item in enumerate(var):
                #creates TSupply1, TSupply2....
                xx_inf.append(key+'{}'.format(i))
            xx.append(var)

        
        # open - how to link names: free variables to inputs?????
        xxx = np.vastak(xx)
        
        # array collapsed into one dimension and ready to use within optimization
        x = xxx.flatten()
        
        # x_init list with two entries: first = flat np array with init values
        # second = corresponding list with variable names
        x_list = [x,xx_inf]
        
        # muefun is the function that returns the updated mue value.. input to the function is iteration counter
        # counter is here 1
        mue = muefun(1)
        
        nr_of_iterations = 666
        
        # performe first optimization
        x_opt = wrapper_sim_opt(x_init = x, x_list = x_list, mue=mue)
        
        #store result values in lists
        mue_result = []
        x_opt_result = []
        
        # iterate and increase mue every time and update x_init
        for i in range(nr_of_iterations-2):
            # start with second iteration
            mue_update = muefun(i+2)
            #update x_list based on new x_opt while x_list should stay the same?!
            x_list = [x_opt, x_list]
            x_opt = wrapper_sim_opt(x_init = x_opt, x_list = x_list, mue=mue_update)
            
            x_opt_result.append(x_opt)
            mue_result.append(mue_update)
    
    
    
    