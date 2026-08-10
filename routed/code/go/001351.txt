package main

import (
	"context"
	"flag"
	"fmt"
	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"
	pb "go-grpc-example/2-simple_rpc/proto"
	"log"
	"time"
)

// Address 连接地址
const Address string = ":8000"


var addr = flag.String("addr", "localhost:50052", "the address to connect to")

var kacp = keepalive.ClientParameters{
	Time:                10 * time.Second, // send pings every 10 seconds if there is no activity
	Timeout:             time.Second,      // wait 1 second for ping ack before considering the connection dead
	PermitWithoutStream: true,             // send pings even without active streams
}

var grpcClient pb.SimpleClient

func main() {
	// 连接服务器
	conn, err := grpc.Dial(Address, grpc.WithInsecure(),grpc.WithKeepaliveParams(kacp))
	if err != nil {
		log.Fatalf("net.Connect err: %v", err)
	}
	defer conn.Close()

	// 建立gRPC连接
	grpcClient = pb.NewSimpleClient(conn)
	route()

	c := pb.NewSimpleClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	fmt.Println("Performing unary request")
	for {
		time.Sleep(5*time.Second)
		res, err := c.UnaryEcho(ctx, &pb.EchoRequest{Message: "keepalive demo"})
		if err != nil {
			log.Fatalf("unexpected error from UnaryEcho: %v", err)
		}
		fmt.Println("RPC response:", res)
	}

	select {} // Block forever; run with GODEBUG=http2debug=2 to observe ping frames and GOAWAYs due to idleness.
}

// route 调用服务端Route方法
func route() {
	// 创建发送结构体
	req := pb.SimpleRequest{
		Data: "grpc",
	}
	// 调用我们的服务(Route方法)
	// 同时传入了一个 context.Context ，在有需要时可以让我们改变RPC的行为，比如超时/取消一个正在运行的RPC
	res, err := grpcClient.Route(context.Background(), &req)
	if err != nil {
		log.Fatalf("Call Route err: %v", err)
	}
	// 打印返回值
	log.Println(res)
}
