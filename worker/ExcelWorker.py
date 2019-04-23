import xlsxwriter
import datetime
import cv2
import os

class ExcelWorker:
    def makeResultFile(self, currentChip, platform, ngList, okList):
        currentDate = datetime.datetime.now()
        workbook = xlsxwriter.Workbook(platform+'_'+currentChip+'_'+currentDate.strftime('%Y%m%d')+'.xlsx')
        worksheet_ng = workbook.add_worksheet('NG List')
        worksheet_ok = workbook.add_worksheet('OK List')
        # TBD: 만약 테스트 안된 List가 있을 경우에만 Add
        #worksheet_na = workbook.add_sheet('NA List')

        title_style = workbook.add_format({'bold': True,
                                            'border': 1,
                                            'align': 'center',
                                            'valign': 'vcenter',
                                            'fg_color': '#cccccc'})
        text_style = workbook.add_format({'bold': True,
                                            'border': 1,
                                            'align': 'center',
                                            'valign': 'vcenter',
                                            'font_color': 'red'})
        subTitle_style = workbook.add_format({'bold': True,
                                            'border': 1,
                                            'align': 'center',
                                            'valign': 'vcenter',
                                            'fg_color': '#eeeeee'})

        worksheet_ng.set_column('A:A', 35)
        worksheet_ng.set_column('B:B', 10)
        worksheet_ng.set_column('C:C', 30)
        worksheet_ng.set_column('D:D', 30)

        worksheet_ok.set_column('A:A', 35)

        # TBD: 역시 조건문 삽입 필요
        #worksheet_na.set_column('A:A', 30)

        worksheet_ng.merge_range('A1:D1','NG List',title_style)
        worksheet_ng.merge_range('A2:D2','Total NG Country Count : {}'.format(len(ngList)),text_style)
        worksheet_ng.write('A3','Country Name',subTitle_style)
        worksheet_ng.write('B3','Ordering Index',subTitle_style)
        worksheet_ng.write('C3','Captured Icon',subTitle_style)
        worksheet_ng.write('D3','Server Icon',subTitle_style)

        worksheet_ok.write('A1','OK List',title_style)
        worksheet_ok.write('A2','Total OK Country Count : {}'.format(len(okList)),text_style)
        worksheet_ok.write('A3','Country Name',subTitle_style)

        startRowCount = 4
        # (country, [[index, cpImgs[index], iconImgs[index]],[...],...])의 list로 ngList 전달됨
        # TBD : 현재 전체 리스트가 아닌 1개만 표현되게 되어있음. 전체 리스트가 필요.
        for item in ngList:
            for detail in item[1]:
                # TBD : 엑셀 전용 이미지 저장할 폴더 만들고 엑셀 생성 후 지워버리기
                #capturedName = str(item[0].split(":")[0].strip())+'_'+str(detail[0])+'_Capture.png'
                captureDir = "download/"+item[0].split(":")[0].strip()+"/"+str(detail[0])+".png"

                #serverIconName = str(item[0])+'_'+str(detail[0])+'_Server.png'
                #cv2.imwrite(capturedName, detail[1])
                #cv2.imwrite(serverIconName, detail[2])
                worksheet_ng.set_row(startRowCount-1, 185)
                worksheet_ng.write('A'+str(startRowCount), str(item[0]), text_style)
                worksheet_ng.write('B'+str(startRowCount), str(detail[0]+1), text_style)
                worksheet_ng.insert_image('C'+str(startRowCount), captureDir, {'positioning': 1, 'x_offset': 10, 'y_offset': 10})
                worksheet_ng.insert_image('D'+str(startRowCount), detail[2][0], {'positioning': 1, 'x_offset': 10, 'y_offset': 10})
                startRowCount += 1

        startRowCount = 4
        for item in okList:
            worksheet_ok.write('A'+str(startRowCount),str(item[0]),text_style)
            startRowCount += 1

        workbook.close()
