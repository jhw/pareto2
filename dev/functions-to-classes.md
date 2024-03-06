I am going to show you some Python functions which take different arguments but return the same structure. I want you to convert them to a class implementation in which the three outputs from each function are replaced by properties for resource_name (string), aws_resource_type (string) and aws_properties (dict). You should create a base class which encapsulates the common parts of these functions. The base class name should reflect the aws_type, particularly the final slug; so a base class which returns AWS::Lambda::Function should be called FunctionBase. Arguments to the functions should be replaced by constructor arguments and saved as instance variables, so that they can be referenced by the property functions. The base class should have default values for every argument. You should create a subclass for each of the functions shown, whose constructor signatures match the function argument signatures. Subclass names should reflect the names in comments above the function body (ignoring pareto, components and __init___ slugs) and the names of the original functions (ignoring init slug). Please maintain these comments above the new class bodies. Each of the functions has the same aws_type, so you will only need an aws_type property in the base class.  All the complexity here is in the aws_properties property. Please return a full code listing that can be copied and pasted and work immediately.
