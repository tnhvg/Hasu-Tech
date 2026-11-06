Attribute VB_Name = "ChaySolver"
' =====================================================================================
' Bai tap tinh huong 3 - Nhom 7 - FIN3002_2
' Macro chay Excel Solver cho toan bo bai:
'   1) Solver 1: danh muc phuong sai nho nhat (Min sigma^2, tong w = 1, w >= 0)
'   2) Solver 3: danh muc duoc chon (Max E(Rp), tong w = 1, sigma_p <= muc chap nhan, w >= 0)
'   3) Solver 2 chay lan luot cho tung muc E(Rp) muc tieu o trang Duong bien,
'      ghi ty trong vao bang va danh dau o cot J.
'
' Cach dung: Alt + F11 -> File -> Import File... chon file nay (hoac Insert -> Module roi dan code)
'            -> dat con tro trong Sub ChayToanBoSolver -> nhan F5.
' Yeu cau: da bat Solver Add-in (File -> Options -> Add-ins -> Excel Add-ins -> Solver Add-in).
'
' Chu thich viet khong dau vi trinh soan VBA tren Windows tieng Anh khong hien chu tieng Viet.
' Cung vi ly do do, trang tinh duoc goi theo so thu tu, khong goi theo ten co dau:
'   6 = Solver 1 - PSNN, 7 = Solver 2 - Duong bien, 8 = Solver 3 - DM chon, 9 = Duong bien
' =====================================================================================
Option Explicit

Private Const TRANG_SOLVER_1 As Integer = 6
Private Const TRANG_SOLVER_2 As Integer = 7
Private Const TRANG_SOLVER_3 As Integer = 8
Private Const TRANG_DUONG_BIEN As Integer = 9
Private Const DONG_DAU_BANG As Long = 5     ' dong dau tien cua bang Duong bien

Public Sub ChayToanBoSolver()
    Dim ma As Variant, ws As Worksheet, wsBien As Worksheet
    Dim r As Long, soLanLoi As Long, mucGoc As Double

    BatSolver
    Application.ScreenUpdating = False

    ' 1) Danh muc phuong sai nho nhat
    ma = GiaiMotTrang(Worksheets(TRANG_SOLVER_1), "$B$16", 2, "")
    If ma > 2 Then soLanLoi = soLanLoi + 1

    ' 2) Danh muc duoc chon: Max E(Rp) voi sigma_p <= B20
    ma = GiaiMotTrang(Worksheets(TRANG_SOLVER_3), "$B$15", 1, "$B$17<=$B$20")
    If ma > 2 Then soLanLoi = soLanLoi + 1

    ' 3) Duong bien: voi moi muc E(Rp) muc tieu, Min sigma^2 voi E(Rp) = muc tieu
    Set ws = Worksheets(TRANG_SOLVER_2)
    Set wsBien = Worksheets(TRANG_DUONG_BIEN)
    mucGoc = ws.Range("B20").Value
    r = DONG_DAU_BANG
    Do While wsBien.Cells(r, 2).Value <> ""
        ws.Range("B20").Value = wsBien.Cells(r, 2).Value
        ma = GiaiMotTrang(ws, "$B$16", 2, "$B$15=$B$20")
        wsBien.Cells(r, 3).Value = ws.Range("B5").Value
        wsBien.Cells(r, 4).Value = ws.Range("C5").Value
        wsBien.Cells(r, 5).Value = ws.Range("D5").Value
        If ma <= 2 Then
            wsBien.Cells(r, 10).Value = "Excel Solver (ma " & ma & ")"
        Else
            wsBien.Cells(r, 10).Value = "Solver bao loi, ma " & ma
            soLanLoi = soLanLoi + 1
        End If
        r = r + 1
    Loop

    ' Tra trang Solver 2 ve diem mau ban dau va giai lai cho khop
    ws.Range("B20").Value = mucGoc
    ma = GiaiMotTrang(ws, "$B$16", 2, "$B$15=$B$20")

    Application.ScreenUpdating = True
    Worksheets(TRANG_DUONG_BIEN).Activate
    If soLanLoi = 0 Then
        MsgBox "Xong: Solver da giai " & (r - DONG_DAU_BANG + 3) & " bai toan, khong co loi." & vbCrLf & _
               "Xem cot J trang Duong bien va trang Danh muc chon.", vbInformation
    Else
        MsgBox "Xong, nhung co " & soLanLoi & " lan Solver bao loi. Xem cot J trang Duong bien.", vbExclamation
    End If
End Sub

' Giai mot trang Solver: dat lai ty trong 1/3, khai bao mo hinh, Solve, giu ket qua.
' loaiToiUu: 1 = Max, 2 = Min.  rangBuocThem: "" hoac dang "$B$15=$B$20", "$B$17<=$B$20".
' Tra ve ma ket qua cua Solver: 0, 1, 2 = tim duoc nghiem; lon hon 2 = co van de.
Private Function GiaiMotTrang(ws As Worksheet, oMucTieu As String, loaiToiUu As Integer, _
                              rangBuocThem As String) As Variant
    ws.Activate
    ws.Range("B5:D5").Value = 1 / 3

    Application.Run "Solver.xlam!SolverReset"
    ' SolverOk(SetCell, MaxMinVal, ValueOf, ByChange, Engine): Engine 1 = GRG Nonlinear
    Application.Run "Solver.xlam!SolverOk", oMucTieu, loaiToiUu, 0, "$B$5:$D$5", 1
    ' SolverAdd(CellRef, Relation, FormulaText): Relation 1 = <=, 2 = =, 3 = >=
    Application.Run "Solver.xlam!SolverAdd", "$E$5", 2, "1"
    Application.Run "Solver.xlam!SolverAdd", "$B$5:$D$5", 3, "0"    ' w >= 0, khong ban khong
    If rangBuocThem <> "" Then
        If InStr(rangBuocThem, "<=") > 0 Then
            Application.Run "Solver.xlam!SolverAdd", Split(rangBuocThem, "<=")(0), 1, Split(rangBuocThem, "<=")(1)
        Else
            Application.Run "Solver.xlam!SolverAdd", Split(rangBuocThem, "=")(0), 2, Split(rangBuocThem, "=")(1)
        End If
    End If
    ' SolverSolve(UserFinish:=True): giai ma khong hien hop thoai ket qua
    GiaiMotTrang = Application.Run("Solver.xlam!SolverSolve", True)
    Application.Run "Solver.xlam!SolverFinish", 1    ' 1 = giu nghiem vua tim duoc
End Function

' Nap Solver Add-in neu chua nap (ten add-in co the khac tren may dung Excel tieng Viet)
Private Sub BatSolver()
    On Error Resume Next
    AddIns("Solver Add-in").Installed = True
    On Error GoTo 0
End Sub
