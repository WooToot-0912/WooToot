using Modbus.Device;
using System.IO.Ports;
using System.Text;

namespace Zhaoxi.SeralPortCommunication
{
    internal class Program
    {
        //.NET Core 5.0~9.0环境下
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");

            //SerialTest();

            NModbus4_ModbusRTU_Test();
        }

        private static void SerialTest()
        {
            SerialPort serialPort = new SerialPort(
                "COM1",
                2400,
                Parity.None,
                8,
                StopBits.One
                );
            //串口通信：
            //指定通信的串口名称
            serialPort.PortName = "COM1"; // 端口号

            //对象的静态方法，不需要实例化直接调用
            //获取当前环境下都有的有效接口名称
            string[] ports = SerialPort.GetPortNames();

            //基本参数，与设备保持一致
            //波特率：发送0101...01的信号，即11个0和1组成的信号，每秒传输多少个
            serialPort.BaudRate = 9600;
            //数据位：8个位数据传输
            serialPort.DataBits = 8;
            //校验位：如果数据位的数量是奇数，则校验位为1，偶数位数据位则校验位为0
            serialPort.Parity = Parity.None;
            //停止位
            serialPort.StopBits = StopBits.One;

            //设置读取超时时间
            serialPort.ReadTimeout = 1000; //读取超时
            //设置发送超时时间
            serialPort.WriteTimeout = 1000; //写入超时

            //设置接收缓冲区大小
            serialPort.ReadBufferSize = 4800;
            //设置发送缓冲区大小
            serialPort.WriteBufferSize = 2048;


            //打开串口（注意：串口被独占）
            serialPort.Open();

            //发送与接收
            SendAndReceive(serialPort);

            //关闭当前使用的串口
            serialPort.Close();

            //当前串口对象的打开状态
            bool state = serialPort.IsOpen;
        }

        //主动发送时：（场景：扫码枪，称重）
        private static void SerialPort_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            //ReadBuffer  有数据 仅仅只是接收数据的时机
            int len = ((SerialPort)sender).BytesToRead;
            byte[] rec_bytes = new byte[len];
            ((SerialPort)sender).Read(rec_bytes, 0, len);
        }

        static void SendAndReceive(SerialPort serialPort)
        {
            //发送功能
            //serialPort.Write("abc123");

            //serialPort.WriteLine();

            string str = "abc123中文";
            byte[] bytes = Encoding.UTF8.GetBytes(str);
            serialPort.Write(bytes, 0, bytes.Length);

            //读取数据功能
            //返回字符串，有数据就拿，没数据就空，不卡线程
            string rec_str = serialPort.ReadExisting();

            //按照缓冲区字节进行接收
            //byte[] rec_bytes = new byte[10];
            //serialPort.Read(rec_bytes,0,10);

            //每调用一次，从缓冲区读取一个字节
            //byte b = (byte)serialPort.ReadByte();

            //serialPort.ReadChar();
            //serialPort.ReadLine();

            //接收到特定字符即返回
            rec_str = serialPort.ReadTo("@");

            //接收缓冲区里可以读取的字节数量
            int len = serialPort.BytesToRead;
            byte[] rec_bytes = new byte[len];
            serialPort.Read(rec_bytes, 0, len);

        }

        private static async Task NModbus4_ModbusRTU_Test()
        {
            SerialPort serialPort = new SerialPort(
                "COM1",
                9600,
                Parity.None,
                8,
                StopBits.One
                );
            serialPort.Open();

            //创建ModbusRTU通信协议对象
            IModbusSerialMaster master = ModbusSerialMaster.CreateRtu(serialPort);

            master.Transport.ReadTimeout = 2000; //读超时
            master.Transport.Retries = 3; //重试次数

            //读取从站5的保持型寄存器0~9
            ushort[] registers = master.ReadHoldingRegisters(
                slaveAddress: 5, //从站地址（1-247)
                startAddress: 0, //起始寄存器地址
                numberOfPoints: 10  //读取寄存器数量
                );

            //异步读取
            //Task<ushort[]> result = master.ReadHoldingRegistersAsync(5, 0, 10);
            //异步第一种处理，所在方法不需要变更异步方法
            //registers = result.GetAwaiter().GetResult();
            //异步第二种处理，所在方法需要变更异步方法
            //ushort[] result = await master.ReadHoldingRegistersAsync(5, 0, 10);
            //查看读取
            Console.WriteLine($"保持型寄存器值：{string.Join(",", registers)}");


            //读取从站5的输入寄存器0~4
            ushort[] inputRegisters = master.ReadInputRegisters(5, 0, 4);
            //inputRegisters = await master.ReadHoldingRegistersAsync(5, 0, 10);
            Console.WriteLine($"输入寄存器值：{string.Join(",", inputRegisters)}");

            //读取从站5的线圈状态0~7
            bool[] coils = master.ReadCoils(5, 0, 8);
            //coils = await master.ReadCoilsAsync(5, 0, 8);
            Console.WriteLine($"线圈状态值：{string.Join(",", coils.Select(c=>c.ToString()))}");

            //读取从站5的输入线圈0~7
            bool[] input = master.ReadInputs(5, 0, 8);
            //input = await master.ReadInputsAsync(5, 0, 8);
            Console.WriteLine($"输入线圈值：{string.Join(",", input.Select(c => c.ToString()))}");

            //向从站5的寄存器5号地址里写入1234   写单个
            // 05
            master.WriteSingleRegister(
                slaveAddress: 5, //从站地址（1-247)
                registerAddress: 5, //寄存器地址
                value: 1234    //写入值
            );

            //向从站5的寄存器0号地址，1号地址，2号地址中依次写入三个数据
            //2字节空间
            // 1：byte  0~255   sbyte   -256 ~ 255
            sbyte v1;
            byte v2;
            // 2: ushort 0~65535   short  -32768~32767
            ushort v3;
            short v4;
            UInt16 v5;
            Int16 v6;
            ushort[] values = { 100, 200, 300 };
            master.WriteMultipleRegisters(1, 0, values);


            // 4:int32  uint32  float 单精度浮点
            //    寄存器一个地址2byte
            float v7 = 4.5f; // byte[4]
            ushort[] datas = new ushort[2];
            //获取浮点型数字对应的字节信息
            byte[] v7_bytes = BitConverter.GetBytes(v7);
            //// 大小端字节序
            //// 0x01  0x2C  大端
            //datas[0] = 0x01;
            //datas[1] = 0x2C;
            //// 0x01  0x2C  小端
            //datas[0] = 0x2C;
            //datas[1] = 0x01;
            // 符合Modbus协议的基本要求  字节序调整，但是最终以设备方要求为准
            Array.Reverse(v7_bytes);

            ushort s1 = (ushort)(v7_bytes[0] * 256 + v7_bytes[1]);
            s1 = BitConverter.ToUInt16(new byte[] { v7_bytes[1], v7_bytes[0] });

            ushort s2 = (ushort)(v7_bytes[2] * 256 + v7_bytes[3]);
            s2 = BitConverter.ToUInt16(new byte[] { v7_bytes[3], v7_bytes[2] });

            datas[0] = s1;
            datas[1] = s2;

            master.WriteMultipleRegisters(5, 8, datas);

            ushort[] fs = master.ReadHoldingRegisters(5, 8, 2);
            byte[] us_bytes_1 = BitConverter.GetBytes(fs[0]);
            byte[] us_bytes_2 = BitConverter.GetBytes(fs[1]);

            byte[] f_bytes = new byte[4] {
                us_bytes_1[1],
                us_bytes_1[0],
                us_bytes_2[1],
                us_bytes_2[0]
            };
            Array.Reverse(f_bytes);
            float f2 = BitConverter.ToSingle(f_bytes, 0);

            //向从站5的0号线圈写入True状态
            master.WriteSingleCoil(5, 0, true);
            //向从站5的5号线圈写入5个状态
            master.WriteMultipleCoils(
                5, 
                5, 
                new bool[] { true, false, true, false, true }
                );

            //异步写单个线圈状态
            //master.WriteSingleCoilAsync();
            //异步写多个线圈状态
            //master.WriteMultipleCoilsAsync();
            //异步写单个寄存器
            //master.WriteSingleRegisterAsync();
            //异步写多个寄存器
            //master.WriteMultipleRegistersAsync();
        }

        private static async Task NModbus4_ModbusASCII_Test()
        {
            SerialPort serialPort = new SerialPort(
                "COM1",
                9600,
                Parity.None,
                8,
                StopBits.One
                );
            serialPort.Open();

            //创建ModbusRTU通信协议对象
            IModbusSerialMaster master = ModbusSerialMaster.CreateAscii(serialPort);

            master.Transport.ReadTimeout = 2000; //读超时
            master.Transport.Retries = 3; //重试次数

            //读取从站5的保持型寄存器0~9
            ushort[] registers = master.ReadHoldingRegisters(
                slaveAddress: 5, //从站地址（1-247)
                startAddress: 0, //起始寄存器地址
                numberOfPoints: 10  //读取寄存器数量
                );

            //异步读取
            //Task<ushort[]> result = master.ReadHoldingRegistersAsync(5, 0, 10);
            //异步第一种处理，所在方法不需要变更异步方法
            //registers = result.GetAwaiter().GetResult();
            //异步第二种处理，所在方法需要变更异步方法
            //ushort[] result = await master.ReadHoldingRegistersAsync(5, 0, 10);
            //查看读取
            Console.WriteLine($"保持型寄存器值：{string.Join(",", registers)}");


            //读取从站5的输入寄存器0~4
            ushort[] inputRegisters = master.ReadInputRegisters(5, 0, 4);
            //inputRegisters = await master.ReadHoldingRegistersAsync(5, 0, 10);
            Console.WriteLine($"输入寄存器值：{string.Join(",", inputRegisters)}");

            //读取从站5的线圈状态0~7
            bool[] coils = master.ReadCoils(5, 0, 8);
            //coils = await master.ReadCoilsAsync(5, 0, 8);
            Console.WriteLine($"线圈状态值：{string.Join(",", coils.Select(c => c.ToString()))}");

            //读取从站5的输入线圈0~7
            bool[] input = master.ReadInputs(5, 0, 8);
            //input = await master.ReadInputsAsync(5, 0, 8);
            Console.WriteLine($"输入线圈值：{string.Join(",", input.Select(c => c.ToString()))}");

            //向从站5的寄存器5号地址里写入1234   写单个
            // 05
            master.WriteSingleRegister(
                slaveAddress: 5, //从站地址（1-247)
                registerAddress: 5, //寄存器地址
                value: 1234    //写入值
            );

            //向从站5的寄存器0号地址，1号地址，2号地址中依次写入三个数据
            //2字节空间
            // 1：byte  0~255   sbyte   -256 ~ 255
            sbyte v1;
            byte v2;
            // 2: ushort 0~65535   short  -32768~32767
            ushort v3;
            short v4;
            UInt16 v5;
            Int16 v6;
            ushort[] values = { 100, 200, 300 };
            master.WriteMultipleRegisters(1, 0, values);


            // 4:int32  uint32  float 单精度浮点
            //    寄存器一个地址2byte
            float v7 = 4.5f; // byte[4]
            ushort[] datas = new ushort[2];
            //获取浮点型数字对应的字节信息
            byte[] v7_bytes = BitConverter.GetBytes(v7);
            //// 大小端字节序
            //// 0x01  0x2C  大端
            //datas[0] = 0x01;
            //datas[1] = 0x2C;
            //// 0x01  0x2C  小端
            //datas[0] = 0x2C;
            //datas[1] = 0x01;
            // 符合Modbus协议的基本要求  字节序调整，但是最终以设备方要求为准
            Array.Reverse(v7_bytes);

            ushort s1 = (ushort)(v7_bytes[0] * 256 + v7_bytes[1]);
            s1 = BitConverter.ToUInt16(new byte[] { v7_bytes[1], v7_bytes[0] });

            ushort s2 = (ushort)(v7_bytes[2] * 256 + v7_bytes[3]);
            s2 = BitConverter.ToUInt16(new byte[] { v7_bytes[3], v7_bytes[2] });

            datas[0] = s1;
            datas[1] = s2;

            master.WriteMultipleRegisters(5, 8, datas);

            ushort[] fs = master.ReadHoldingRegisters(5, 8, 2);
            byte[] us_bytes_1 = BitConverter.GetBytes(fs[0]);
            byte[] us_bytes_2 = BitConverter.GetBytes(fs[1]);

            byte[] f_bytes = new byte[4] {
                us_bytes_1[1],
                us_bytes_1[0],
                us_bytes_2[1],
                us_bytes_2[0]
            };
            Array.Reverse(f_bytes);
            float f2 = BitConverter.ToSingle(f_bytes, 0);

            //向从站5的0号线圈写入True状态
            master.WriteSingleCoil(5, 0, true);
            //向从站5的5号线圈写入5个状态
            master.WriteMultipleCoils(
                5,
                5,
                new bool[] { true, false, true, false, true }
                );

            //异步写单个线圈状态
            //master.WriteSingleCoilAsync();
            //异步写多个线圈状态
            //master.WriteMultipleCoilsAsync();
            //异步写单个寄存器
            //master.WriteSingleRegisterAsync();
            //异步写多个寄存器
            //master.WriteMultipleRegistersAsync();
        }
    }
}
