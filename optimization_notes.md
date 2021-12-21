
## __Structured Optimization Modeling with Pyomo and Coopr__
https://www.youtube.com/watch?v=cjMkVHjhSBI

* COOPR = COmmon Optimization Python Repository
* PYOMO = PYthon Optimization Modeling Objects
  * PYOMO is the core algebraic component
  * COOPR builds in more solvers and extensions

### PYOMO Overview:
* Separates model from data - can pull in data from elsewhere after building model
* Not built for speed - built for flexibility
* "Meta-solver" - calls other solvers
* Object-based and grounded in Python
* Complete model consists of:
  * Definition as concrete/abstract model
  * Definition of variables
  * Objective function and "sense" (e.g. minimize)
* Call "pyomo" command and tell which solver you want to solve
* Everything built on top of coopr --> import coopr.pyomo to avoid verbosity

### The Model
* From coopr.pyomo import * tells Python you want the Pyomo modeling environment
* Start by defining model as concrete or abstract
  * Concrete model must have data present when components are defined
  * Name your model "model" unless you want to tell Pyomo what it's called via command line
    * model = ConcreteModel()
* Define variables
  * Scalar: model.x = var(initialize = K, within = _domain_, bounds = _(a, b)_)
    * Within is optional and sents domain for variable (e.g. NonNegativeReals, Binary, etc.)
    * Variable names within model must be unique
    * If domain and bounds are empty, assumed to be all real numbers
      * Domain and bounds are pretty much the same thing, just coded differently
    * K here is some initial value of your variable
  * Indexed: model.y_vector = Var(IDX), model.y_matrix = Var(IDX_1, IDX_2)
    * Variable is indexed over some iterable object, such as a list or a set
* Define objective function
  * model.obj = Objective(expr(1-model.x) + 2*model.y, sense = minimize)
    * Expr is some expression or function-like object that gives an expression that you are trying to minimize (or whatever else your sense dictates)
      * Not relational!
      * Default sense is minimization

### Constraints
* Relational expressions (>, <, =, etc.)
* model.c = Constraint(expr = model.x > model.y*2)
  * Similar to above, expr is some expression or function-like objective
  * Often use list comprehensions when using indexed variables in constraint
  * If constraint is a tuple,
    * Three items in the tuple means (lowerbound, expression, upperbound)
    * Two items in the tuple means (A, B) are equal
  * Constraint lists allows multiple constraints in model - don't have to be related
    * model.c.add(new constraint) allows you to add constraint to lists
  * Define as rule first in abstract model

### Indices
* Sets useful for managing multi-dimensional Indices
  * Note that Pyomo uses "Set", which is different from a Python "set"
    * Set(initialize = [a, b, c]) <- note that "initialize" needs to be there
  * RangeSet gives sequential integers as your index

### Parameters
* model.param = Param(index = IDX, initialize = K, mutable = True)
  * "mutable" signifies whether you can later change this parameter (e.g. sensitivity analysis)
* Params can get data from external sources such as a .dat, .xlsx, or .csv
  * import mydata.xls range=ABC : Z=[A, B], Y = C

  ## __ Introduction to Math Modeling in Python __
  https://www.youtube.com/watch?v=pxCogCylmKs

### Overview
* Pyomo for defining model - not a solver
    * Supports many solvers
* Matrix/vector operations require messing with the indices - doesn't do it for you
* Vars, objective, constraints must be attached to modeling
  * Params, vars feed constraints and Objective
  * Constraints, objective, params, variables can be fed in as sets - set must be defined first
    * There is a nice chronology diagram at 6:40


## _ND Pyomo Cookbook_
https://jckantor.github.io/ND-Pyomo-Cookbook/

### Overview
* Model consists of:
  * Decision variables
  * Constraints
  * Objective
    































.
