disp(sprintf('%s: randomizing rand initial state',which('startup.m')))
rand('twister',sum(100*clock))
setenv('OMP_NUM_THREADS','1')
set(0,'DefaultTextInterpreter','none')
disp(sprintf('%s: %d CPUs detected, using %s threads',which('startup.m'),feature('numCores'),getenv('OMP_NUM_THREADS')))

% Set some standard warnings to off
% Note: set this temporary to false if you a looking for an "weird" error.
% Set it to true if you are annoyed by too many warnings (on your own risk).  
if false
    warning off MATLAB:divideByZero
    warning off MATLAB:log:LogOfZero
    warning off all
    fprintf('%s: disabling all warnings\n',mfilename)
end
