#!/usr/bin/env wolframscript

(*
Wolfram Language script for chess position evaluation and move analysis.

This script provides comprehensive chess analysis using Wolfram's
computational capabilities including pattern recognition, tactical
analysis, and strategic evaluation.

Usage:
    wolframscript -file wolfram_evaluation.wl input.json
    wolframscript -file wolfram_evaluation.wl --position-analysis input.json
*)

Begin["`ChessEvaluation`"];

(* Global variables for analysis *)
$pieceValues = <|
    "P" -> 1, "R" -> 5, "N" -> 3, "B" -> 3, "Q" -> 9, "K" -> 100,
    "p" -> -1, "r" -> -5, "n" -> -3, "b" -> -3, "q" -> -9, "k" -> -100
|>;

$centerSquares = {{4, 4}, {4, 5}, {5, 4}, {5, 5}};
$kingSafetySquares = {{1, 1}, {1, 2}, {1, 3}, {2, 1}, {2, 2}, {2, 3}, {3, 1}, {3, 2}, {3, 3}};

(* Parse FEN string to board representation *)
parseFEN[fen_String] := Module[{parts, board, rank, file, char},
    parts = StringSplit[fen, " "];
    board = ConstantArray[None, {8, 8}];
    rank = 8;
    file = 1;
    
    Do[
        Switch[char,
            "/", (* Next rank *)
                rank--; file = 1,
            _?DigitQ, (* Empty squares *)
                file += ToExpression[char],
            _?LetterQ, (* Piece *)
                board[[rank, file]] = char;
                file++
        ],
        {char, Characters[parts[[1]]]}
    ];
    
    board
];

(* Convert board coordinates to algebraic notation *)
coordsToAlgebraic[{rank_, file_}] := StringJoin[
    FromCharacterCode[96 + file],
    ToString[9 - rank]
];

(* Convert algebraic notation to board coordinates *)
algebraicToCoords[square_String] := Module[{file, rank},
    file = ToCharacterCode[square[[1]]] - 96;
    rank = 9 - ToExpression[square[[2]]];
    {rank, file}
];

(* Get piece at given coordinates *)
getPiece[board_List, {rank_, file_}] := 
    If[1 <= rank <= 8 && 1 <= file <= 8, board[[rank, file]], None];

(* Check if square is under attack *)
isUnderAttack[board_List, {rank_, file_}, color_String] := Module[{
    piece, attackerColor, directions, i, j, newRank, newFile
},
    piece = getPiece[board, {rank, file}];
    If[piece === None, Return[False]];
    
    attackerColor = If[color === "white", "black", "white"];
    
    (* Check for pawn attacks *)
    If[color === "white",
        (* White pawns attack diagonally up *)
        Do[
            newRank = rank - 1; newFile = file + dir;
            If[getPiece[board, {newRank, newFile}] === "p", Return[True]],
            {dir, {-1, 1}}
        ],
        (* Black pawns attack diagonally down *)
        Do[
            newRank = rank + 1; newFile = file + dir;
            If[getPiece[board, {newRank, newFile}] === "P", Return[True]],
            {dir, {-1, 1}}
        ]
    ];
    
    (* Check for knight attacks *)
    Do[
        newRank = rank + i; newFile = file + j;
        If[getPiece[board, {newRank, newFile}] === If[color === "white", "n", "N"], 
           Return[True]],
        {i, {-2, -1, 1, 2}}, {j, {-2, -1, 1, 2}}
    ];
    
    (* Check for rook/queen attacks *)
    directions = {{-1, 0}, {1, 0}, {0, -1}, {0, 1}};
    Do[
        i = 1;
        While[True,
            newRank = rank + i * dir[[1]];
            newFile = file + i * dir[[2]];
            piece = getPiece[board, {newRank, newFile}];
            If[piece === None, Break[]];
            If[piece === If[color === "white", "r", "R"] || 
               piece === If[color === "white", "q", "Q"], Return[True]];
            If[piece =!= None, Break[]];
            i++
        ],
        {dir, directions}
    ];
    
    (* Check for bishop/queen attacks *)
    directions = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}};
    Do[
        i = 1;
        While[True,
            newRank = rank + i * dir[[1]];
            newFile = file + i * dir[[2]];
            piece = getPiece[board, {newRank, newFile}];
            If[piece === None, Break[]];
            If[piece === If[color === "white", "b", "B"] || 
               piece === If[color === "white", "q", "Q"], Return[True]];
            If[piece =!= None, Break[]];
            i++
        ],
        {dir, directions}
    ];
    
    (* Check for king attacks *)
    Do[
        newRank = rank + i; newFile = file + j;
        If[getPiece[board, {newRank, newFile}] === If[color === "white", "k", "K"], 
           Return[True]],
        {i, {-1, 0, 1}}, {j, {-1, 0, 1}}
    ];
    
    False
];

(* Calculate material balance *)
calculateMaterial[board_List] := Module[{total},
    total = 0;
    Do[
        If[board[[i, j]] =!= None,
            total += $pieceValues[board[[i, j]]]
        ],
        {i, 1, 8}, {j, 1, 8}
    ];
    total
];

(* Calculate piece mobility *)
calculateMobility[board_List, color_String] := Module[{mobility, piece, directions},
    mobility = 0;
    
    Do[
        piece = board[[i, j]];
        If[piece =!= None && 
           ((color === "white" && UpperCaseQ[piece]) || 
            (color === "black" && LowerCaseQ[piece])),
            
            (* Count legal moves for this piece *)
            directions = Switch[piece,
                "P" | "p", {{-1, 0}, {-1, -1}, {-1, 1}},
                "R" | "r", {{-1, 0}, {1, 0}, {0, -1}, {0, 1}},
                "N" | "n", {{-2, -1}, {-2, 1}, {-1, -2}, {-1, 2}, {1, -2}, {1, 2}, {2, -1}, {2, 1}},
                "B" | "b", {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}},
                "Q" | "q", {{-1, -1}, {-1, 0}, {-1, 1}, {0, -1}, {0, 1}, {1, -1}, {1, 0}, {1, 1}},
                "K" | "k", {{-1, -1}, {-1, 0}, {-1, 1}, {0, -1}, {0, 1}, {1, -1}, {1, 0}, {1, 1}},
                _, {}
            ];
            
            Do[
                newRank = i + dir[[1]];
                newFile = j + dir[[2]];
                If[1 <= newRank <= 8 && 1 <= newFile <= 8,
                    targetPiece = getPiece[board, {newRank, newFile}];
                    If[targetPiece === None || 
                       ((color === "white" && LowerCaseQ[targetPiece]) || 
                        (color === "black" && UpperCaseQ[targetPiece])),
                        mobility++
                    ]
                ],
                {dir, directions}
            ]
        ],
        {i, 1, 8}, {j, 1, 8}
    ];
    
    mobility
];

(* Calculate king safety *)
calculateKingSafety[board_List, color_String] := Module[{
    kingPos, safety, i, j, square
},
    (* Find king position *)
    kingPos = None;
    Do[
        If[board[[i, j]] === If[color === "white", "K", "k"],
            kingPos = {i, j}; Break[]
        ],
        {i, 1, 8}, {j, 1, 8}
    ];
    
    If[kingPos === None, Return[0]];
    
    safety = 0;
    
    (* Check squares around king *)
    Do[
        square = {kingPos[[1]] + i, kingPos[[2]] + j};
        If[1 <= square[[1]] <= 8 && 1 <= square[[2]] <= 8,
            If[isUnderAttack[board, square, color],
                safety -= 10  (* Penalty for attacked squares *)
            ]
        ],
        {i, -1, 1}, {j, -1, 1}
    ];
    
    safety
];

(* Calculate center control *)
calculateCenterControl[board_List, color_String] := Module[{control, square},
    control = 0;
    
    Do[
        square = $centerSquares[[i]];
        piece = getPiece[board, square];
        If[piece =!= None && 
           ((color === "white" && UpperCaseQ[piece]) || 
            (color === "black" && LowerCaseQ[piece])),
            control += 2
        ],
        {i, Length[$centerSquares]}
    ];
    
    control
];

(* Evaluate a single move *)
evaluateMove[board_List, move_String, color_String] := Module[{
    fromSquare, toSquare, fromCoords, toCoords, piece, capturedPiece,
    materialGain, mobilityGain, safetyGain, centerGain, totalScore
},
    (* Parse move *)
    fromSquare = StringTake[move, 2];
    toSquare = StringTake[move, 3;;4];
    fromCoords = algebraicToCoords[fromSquare];
    toCoords = algebraicToCoords[toSquare];
    
    piece = getPiece[board, fromCoords];
    capturedPiece = getPiece[board, toCoords];
    
    (* Material evaluation *)
    materialGain = 0;
    If[capturedPiece =!= None,
        materialGain = $pieceValues[capturedPiece]
    ];
    
    (* Mobility evaluation *)
    mobilityGain = 0;
    (* This is simplified - in practice would need to calculate actual mobility change *)
    
    (* Safety evaluation *)
    safetyGain = 0;
    (* Simplified safety evaluation *)
    
    (* Center control *)
    centerGain = 0;
    If[MemberQ[$centerSquares, toCoords],
        centerGain = 1
    ];
    
    (* Combine scores *)
    totalScore = materialGain + 0.1 * mobilityGain + 0.2 * safetyGain + 0.3 * centerGain;
    
    totalScore
];

(* Main evaluation function *)
evaluatePosition[board_List, color_String] := Module[{
    material, mobility, kingSafety, centerControl, totalScore
},
    material = calculateMaterial[board];
    mobility = calculateMobility[board, color];
    kingSafety = calculateKingSafety[board, color];
    centerControl = calculateCenterControl[board, color];
    
    totalScore = material + 0.1 * mobility + 0.2 * kingSafety + 0.1 * centerControl;
    
    Association[
        "material" -> material,
        "mobility" -> mobility,
        "king_safety" -> kingSafety,
        "center_control" -> centerControl,
        "total_score" -> totalScore
    ]
];

(* Main processing function *)
processMoves[inputFile_String] := Module[{
    data, board, moves, color, evaluations, move, score
},
    (* Load input data *)
    data = Import[inputFile, "JSON"];
    board = parseFEN[data["fen"]];
    moves = data["moves"];
    color = If[StringContainsQ[data["fen"], " w "], "white", "black"];
    
    (* Evaluate each move *)
    evaluations = Association[];
    Do[
        score = evaluateMove[board, move, color];
        evaluations[move] = score
    , {move, moves}];
    
    (* Return as JSON *)
    ExportString[evaluations, "JSON"]
];

(* Position analysis function *)
analyzePosition[inputFile_String] := Module[{
    data, board, color, analysis
},
    (* Load input data *)
    data = Import[inputFile, "JSON"];
    board = parseFEN[data["fen"]];
    color = If[StringContainsQ[data["fen"], " w "], "white", "black"];
    
    (* Perform analysis *)
    analysis = evaluatePosition[board, color];
    
    (* Add additional analysis *)
    analysis["fen"] = data["fen"];
    analysis["color"] = color;
    analysis["analysis_timestamp"] = DateString[];
    
    (* Return as JSON *)
    ExportString[analysis, "JSON"]
];

End[];

(* Main execution *)
main[args_List] := Module[{inputFile, isPositionAnalysis},
    If[Length[args] < 2,
        Print["Usage: wolframscript -file wolfram_evaluation.wl [--position-analysis] input.json"];
        Return[$Failed];
    ];
    
    isPositionAnalysis = MemberQ[args, "--position-analysis"];
    inputFile = Last[args];
    
    If[!FileExistsQ[inputFile],
        Print["Error: Input file not found: ", inputFile];
        Return[$Failed];
    ];
    
    If[isPositionAnalysis,
        Print[analyzePosition[inputFile]],
        Print[processMoves[inputFile]]
    ];
];

(* Execute main function *)
main[$CommandLine];