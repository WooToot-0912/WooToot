using Modbus.Device;
using System.Net;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Text;

namespace Zhaoxi.SocketCommunication
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");

            //SocketServerTest();

            //SocketClientest();

            //SocketUdpTest();

            //TcpClientTest();

            //TcpListenerTest();

            ModbusTCP_Test();

            Console.ReadLine();

        }

        static void SocketServerTest()
        {
            //1.对象创建 Socket
            Socket server = new Socket(
                AddressFamily.InterNetwork, //可选，默认IPV4，可以省略
                SocketType.Stream, 
                ProtocolType.Tcp
            );

            //2.绑定本地IP和端口
            IPEndPoint localEndPoint = new IPEndPoint(IPAddress.Any, 8888);
            server.Bind(localEndPoint);

            //3.开启监听,最大等待连接数设为 10
            //** 并不是只能连10个客户端，可以设置更大的值 **
            server.Listen(10);
            Console.WriteLine("服务器已启动，等待客户端连接...");

            //4.接收客户端连接
            while (true)
            {
                Socket client = server.Accept();
                Console.WriteLine($"客户端已连接:{client.RemoteEndPoint}");

                //5.接收数据
                byte[] buffer = new byte[1024];
                Task.Factory.StartNew(() => 
                {
                    while (true)
                    {
                        int bytesRead = client.Receive(buffer);
                        string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                        Console.WriteLine($"客户端发送的数据:{message}");

                        //6.发送响应
                        string response = "Hello WooToot！";
                        client.Send(Encoding.UTF8.GetBytes(response));
                    }
                });       
            }

            //7.关闭连接
            //client.Close();
            //server.Close();


        }

        static void SocketClientest()
        {
            //1.创建 Socket 对象
            Socket clientSocket = new Socket(
                AddressFamily.InterNetwork, //可选，默认IPV4，可以省略
                SocketType.Stream,
                ProtocolType.Tcp
            );

            //2.连接到服务器
            IPEndPoint serverEndPoint = new IPEndPoint(IPAddress.Parse("127.0.0.1"), 8888);
            //TCP连接的三次握手（对应的：断开的四次挥手）
            clientSocket.Connect(serverEndPoint);
            Console.WriteLine($"客户端已连接到服务器:{serverEndPoint}");

            //3.发送数据
            string message = "Hello Server!";
            byte[] msg_bytes = Encoding.UTF8.GetBytes(message);
            clientSocket.Send(msg_bytes);

            //4.接收响应
            byte[] buffer = new byte[1024];
            int bytesRead = clientSocket.Receive(buffer);
            string response = Encoding.UTF8.GetString(buffer, 0, bytesRead);
            Console.WriteLine($"服务器响应数据:{response}");

            buffer = new byte[1024];
            bytesRead = clientSocket.Receive(buffer);
            response = Encoding.UTF8.GetString(buffer, 0, bytesRead);
            Console.WriteLine($"服务器响应数据:{response}");

            //（1）长数据的接收 做长度的标记
            //（2）多余的数据  可以再接收

            //5.关闭连接
            //clientSocket.Close();
        }

        static void SocketUdpTest()
        {
            // UDP 服务端
            Socket udp = new Socket(
                AddressFamily.InterNetwork,
                SocketType.Dgram,
                ProtocolType.Udp
                );

            udp.Bind(new IPEndPoint(IPAddress.Any, 9999));

            //1.指定地址
            EndPoint endPoint = new IPEndPoint(IPAddress.Parse("127.0.0.1"), 9999);
            udp.SendTo(Encoding.UTF8.GetBytes("Hello, UDP!"), endPoint);
            //接收
            byte[] buffer = new byte[1024];
            endPoint = new IPEndPoint(IPAddress.Any, 0);
            //参数接收数据的来源
            int bytesRead = udp.ReceiveFrom(buffer, ref endPoint);
            string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
            Console.WriteLine($"接收到来自{endPoint}的消息:{message}");

            //2.广播模式 UDP 客户端
            udp.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.Broadcast, true);
            endPoint = new IPEndPoint(IPAddress.Parse("255.255.255.255"), 12345);
            udp.SendTo(Encoding.UTF8.GetBytes("Hello, UDP!-Broadcast"), endPoint);
        }

        static void TcpClientTest()
        {
            //1.创建 TcpClient 并连接到服务器
            TcpClient client = new TcpClient();
            
            client.Connect("127.0.0.1", 8888);
            Console.WriteLine($"已连接到服务器");

            //2.获取网络流
            NetworkStream stream = client.GetStream();

            //3.发送数据
            string message = "Hello Client!";
            byte[] sendData = Encoding.UTF8.GetBytes(message);
            stream.Write(sendData, 0, sendData.Length);
            Console.WriteLine($"已发送数据:{message}");

            //4.接收响应
            byte[] buffer = new byte[1024];
            int bytesRead = stream.Read(buffer, 0, buffer.Length);
            string response = Encoding.UTF8.GetString(buffer, 0, bytesRead);
            Console.WriteLine($"接收到响应数据:{response}");
        }

        static void TcpListenerTest()
        {
            TcpListener server = new TcpListener(IPAddress.Any, 8888);
            server.Start();
            Console.WriteLine("服务器已启动，等待客户端连接...");

            try
            {
                //1.接受客户端连接
                using (TcpClient client = server.AcceptTcpClient())
                {
                    Console.WriteLine($"客户端已连接:{((IPEndPoint)client.Client.RemoteEndPoint).Address}");

                    //2.获取网络流
                    NetworkStream stream = client.GetStream();

                    //3.接收数据
                    byte[] buffer = new byte[1024];
                    int bytesRead = stream.Read(buffer, 0, buffer.Length);
                    string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    Console.WriteLine($"接收到响应数据:{message}");

                    //4.发送响应
                    string response = "Hello Client!";
                    byte[] sendData = Encoding.UTF8.GetBytes(response);
                    stream.Write(sendData, 0, sendData.Length);
                    Console.WriteLine($"已发送数据:{response}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"错误：{ex.Message}");
            }
            finally
            {
                server.Stop();
                Console.WriteLine("服务器已停止");
            }
            
        }

        static void ModbusTCP_Test()
        {
            TcpClient tcpClient = new TcpClient();
            tcpClient.Connect("127.0.0.1", 502);
            //创建ModbusRTU通信协议对象
            ModbusMaster master = ModbusIpMaster.CreateIp(tcpClient);

            master.Transport.ReadTimeout = 2000; //读超时
            master.Transport.Retries = 3; //重试次数


            //关于主站读取的相关方法
            //-------------------------------------------------
            //读取从站1的保持型寄存器0~9
            ushort[] registers = master.ReadHoldingRegisters(
                slaveAddress: 1, //从站地址（1-247)
                startAddress: 0, //起始寄存器地址
                numberOfPoints: 10  //读取寄存器数量
            );

            //异步读取
            //Task<ushort[]> result = master.ReadHoldingRegistersAsync(1, 0, 10);
            //异步第一种处理，所在方法不需要变更异步方法
            //registers = result.GetAwaiter().GetResult();
            //异步第二种处理，所在方法需要变更异步方法 (需要方法改成async Task返回）
            //ushort[] result = await master.ReadHoldingRegistersAsync(1, 0, 10);
            //查看读取
            Console.WriteLine($"保持型寄存器值：{string.Join(",", registers)}");

            //读取从站1的输入寄存器0~4
            ushort[] inputRegisters = master.ReadInputRegisters(1, 0, 4);
            //inputRegisters = await master.ReadHoldingRegistersAsync(5, 0, 10);
            Console.WriteLine($"输入寄存器值：{string.Join(",", inputRegisters)}");

            //读取从站1的线圈状态0~7
            bool[] coils = master.ReadCoils(1, 0, 8);
            //coils = await master.ReadCoilsAsync(5, 0, 8);
            Console.WriteLine($"线圈状态值：{string.Join(",", coils.Select(c => c.ToString()))}");

            //读取从站1的输入线圈0~7
            bool[] input = master.ReadInputs(1, 0, 8);
            //input = await master.ReadInputsAsync(5, 0, 8);
            Console.WriteLine($"输入线圈值：{string.Join(",", input.Select(c => c.ToString()))}");



            //关于主站写入的相关方法
            //-------------------------------------------------
            //向从站的寄存器5号地址里写入1234   写单个
            master.WriteSingleRegister(
                slaveAddress: 1, //从站地址（1-247)
                registerAddress: 5, //寄存器地址
                value: 1234    //写入值
            );

            //向从站1的寄存器0号地址，1号地址，2号地址中依次写入三个数据
            ushort[] values = { 100, 200, 300 };
            master.WriteMultipleRegisters(1, 0, values);

            //向从站1的0号线圈写入True状态
            master.WriteSingleCoil(1, 0, true);
            //向从站1的5号线圈写入5个状态
            master.WriteMultipleCoils(
                1,
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
