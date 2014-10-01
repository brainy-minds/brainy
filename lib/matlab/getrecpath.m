function res = getrecpath(value)
%ADDRECPATH Splits pathnames with ':', recursively generates path for each
% folder and concatenates them together.
%
pathFolds = cellfun(@genpath, strsplit(value,':'), 'UniformOutput', false);
res = '';
for index = 1:numel(pathFolds)
    res = strcat(res, pathFolds{index});
end
end
