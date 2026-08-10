package dev.anyroad.threadlocal;

import com.alibaba.ttl.TransmittableThreadLocal;
import com.alibaba.ttl.threadpool.TtlExecutors;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.fail;

@Slf4j
public class TransmittableThreadLocalTest {
    @Test
    @DisplayName("Test basic TransmittableThreadLocal behavior - get value in the child thread")
    public void transmittableThreadLocalBasic() throws InterruptedException {
        ThreadLocal<String> threadLocal = new TransmittableThreadLocal<>();

        String mainThreadData = "main thread";
        threadLocal.set(mainThreadData);

        ThreadLocalData dataFromChildThread = new ThreadLocalData("original data");

        Thread childThread = new Thread(() -> dataFromChildThread.setData(threadLocal.get()));

        childThread.start();
        childThread.join();

        assertEquals(mainThreadData, dataFromChildThread.getData());
    }

    @Test
    @DisplayName("Modify value in parent ThreadLocal after starting child thread")
    public void inheritableThreadChangeInParentThread() throws InterruptedException {
        ThreadLocal<String> threadLocal = new TransmittableThreadLocal<>();

        String mainThreadData = "main thread";
        threadLocal.set(mainThreadData);

        ThreadLocalData dataFromChildThread = new ThreadLocalData("original data");

        CountDownLatch threadStartedLatch = new CountDownLatch(1);
        CountDownLatch valueChangedLatch = new CountDownLatch(1);

        Thread childThread = new Thread(() -> {
            threadStartedLatch.countDown();
            try {
                valueChangedLatch.await();
            } catch (InterruptedException e) {
                fail("Exception during latch await: " + e);
            }
            dataFromChildThread.setData(threadLocal.get());

        });

        childThread.start();

        threadStartedLatch.await();

        threadLocal.set("main new thread");
        valueChangedLatch.countDown();

        childThread.join();

        assertEquals(mainThreadData, dataFromChildThread.getData());
    }

    @Test
    @DisplayName("Thread created in Thread Pool inherit value")
    public void transmittableThreadLocalWithThreadPool() throws InterruptedException {
        ThreadLocal<String> threadLocal = new TransmittableThreadLocal<>();

        String mainThreadData = "main thread";
        threadLocal.set(mainThreadData);

        ThreadLocalData dataFromChildThread = new ThreadLocalData("original data");

        ExecutorService executorService = TtlExecutors.getTtlExecutorService(Executors.newSingleThreadExecutor());
        executorService.submit(() -> dataFromChildThread.setData(threadLocal.get()));
        executorService.shutdown();
        executorService.awaitTermination(1, TimeUnit.SECONDS);

        assertEquals(mainThreadData, dataFromChildThread.getData());
    }

    @Test
    @DisplayName("Second runnable submitted to Thread Pool gets updated value")
    public void transmittableThreadLocalWithThreadPoolSecondRunnable() throws InterruptedException, ExecutionException {
        ThreadLocal<String> threadLocal = new TransmittableThreadLocal<>();

        String mainOriginalThreadData = "main thread";
        threadLocal.set(mainOriginalThreadData);

        ThreadLocalData dataFromChildThread = new ThreadLocalData("original data");

        ExecutorService executorService = TtlExecutors.getTtlExecutorService(Executors.newSingleThreadExecutor());

        Future<?> future = executorService.submit(() -> {
            dataFromChildThread.setData(threadLocal.get());
        });

        future.get();

        assertEquals(mainOriginalThreadData, dataFromChildThread.getData());

        String mainNewThreadData = "main new thread";
        threadLocal.set(mainNewThreadData);

        executorService.submit(() -> dataFromChildThread.setData(threadLocal.get()));

        executorService.shutdown();
        executorService.awaitTermination(1, TimeUnit.SECONDS);

        assertEquals(mainNewThreadData, dataFromChildThread.getData());
    }

}
