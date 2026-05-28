import { NextResponse } from 'next/server';
import PDFDocument from 'pdfkit';
import path from 'path';
import fs from 'fs';

export async function GET() {
  try {
    console.log('开始生成PDF...');
    
    // 创建 PDF 文档
    const doc = new PDFDocument({
      size: 'A4',
      margin: 50,
      autoFirstPage: true,
      bufferPages: false
    });

    // 使用Buffer方式收集PDF数据
    const pdfBuffer: Buffer = await new Promise((resolve, reject) => {
      const buffers: Buffer[] = [];
      
      doc.on('data', (chunk: Buffer) => {
        buffers.push(chunk);
      });
      
      doc.on('end', () => {
        const pdfData = Buffer.concat(buffers);
        resolve(pdfData);
      });
      
      doc.on('error', (error) => {
        reject(error);
      });

      try {
        const fontPath = path.join(process.cwd(), 'public', 'fonts', 'NotoSansSC-Bold.ttf');
        if (fs.existsSync(fontPath)) {
          doc.font(fontPath);
        }

        // 设置字体大小
        doc.fontSize(24);
        
        // 添加标题
        doc.text('Hello World!', 50, 100);
        
        // 添加一些中文内容
        doc.fontSize(16);
        doc.text('这是一个简单的PDF测试文件', 50, 150);
        doc.text('使用PDFKit生成，支持中文显示', 50, 180);
        
        // 添加更多中文内容
        doc.fontSize(14);
        doc.text('测试中文字体：', 50, 220);
        doc.text('你好，世界！', 50, 250);
        doc.text('这是一个测试文档', 50, 280);
        
        // 添加当前时间
        doc.fontSize(12);
        doc.text(`生成时间: ${new Date().toLocaleString('zh-CN')}`, 50, 320);
        
        // 完成 PDF
        doc.end();
        console.log('PDF生成完成');
      } catch (error) {
        console.error('PDF生成过程中出错:', error);
        reject(error);
      }
    });

    // 设置响应头
    const headers = new Headers();
    headers.set('Content-Type', 'application/pdf');
    headers.set('Content-Disposition', 'attachment; filename=hello.pdf');
    headers.set('Content-Length', pdfBuffer.length.toString());

    return new NextResponse(pdfBuffer, { headers });
  } catch (error) {
    console.error('PDF 生成失败:', error);
    return NextResponse.json({ 
      error: 'PDF 生成失败', 
      details: error instanceof Error ? error.message : String(error) 
    }, { status: 500 });
  }
}
