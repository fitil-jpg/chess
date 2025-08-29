#!/usr/bin/env wolframscript

(* Generate heatmaps from a CSV table of piece moves.
   The script mirrors the options of the R implementation and
   writes CSV, JSON and PNG files for each piece. *)

args = Rest[$ScriptCommandLine];
opts = <|"palette" -> "Reds", "bins" -> 8, "resolution" -> 300|>;
input = None;
i = 1;
While[i <= Length[args],
  arg = args[[i]];
  If[StringStartsQ[arg, "--"],
    Switch[arg,
      "--palette", i++; opts["palette"] = args[[i]],
      "--bins", i++; opts["bins"] = ToExpression[args[[i]]],
      "--resolution", i++; opts["resolution"] = ToExpression[args[[i]]],
      _, Null
    ],
    If[input === None, input = arg]
  ];
  i++;
];

If[input === None,
  Print["Usage: generate_heatmaps.wl [--palette name] [--bins n] [--resolution dpi] <moves.csv>"];
  Exit[1]
];

moves = Import[input];
headers = First[moves];
rows = Rest[moves];
records = AssociationThread[headers, #] & /@ rows;

letterToNum = AssociationThread[{"a", "b", "c", "d", "e", "f", "g", "h"} -> Range[8]];

grouped = GroupBy[records, #piece &];
outDir = DirectoryName[input];
binFun = Function[{val}, Ceiling[val*opts["bins"]/8]];

Do[
  pieceRecords = grouped[piece];
  files = letterToNum[StringTake[#to, 1]] & /@ pieceRecords;
  ranks = ToExpression[StringTake[#to, 2]] & /@ pieceRecords;
  fileBins = binFun /@ files;
  rankBins = binFun /@ ranks;
  mat = ConstantArray[0, {opts["bins"], opts["bins"]}];
  Do[
    mat[[rankBins[[k]], fileBins[[k]]]]++,
    {k, Length[fileBins]}
  ];
  csvPath = FileNameJoin[{outDir, "heatmap_" <> piece <> "_bins" <> ToString[opts["bins"]] <> ".csv"}];
  jsonPath = FileNameJoin[{outDir, "heatmap_" <> piece <> "_bins" <> ToString[opts["bins"]] <> ".json"}];
  pngPath = FileNameJoin[{outDir, "heatmap_" <> piece <> "_bins" <> ToString[opts["bins"]] <> ".png"}];
  Export[csvPath, mat];
  Export[jsonPath, mat, "JSON", "Compact" -> False];
  plot = ArrayPlot[Reverse[mat], ColorFunction -> ColorData[opts["palette"]],
    Frame -> False, ColorFunctionScaling -> True];
  Export[pngPath, plot, ImageResolution -> opts["resolution"]];
  , {piece, Keys[grouped]}];
