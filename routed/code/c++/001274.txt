#include "Image/motionAlgorithms/IAlertAlgorithm.hpp"
#include "Image/private/CRingBuffer.hpp"

CImageBuffer::CRingBuffer::CRingBuffer(int size, int longSize, int longSkipCount, const std::string& info)
    : mMaxSize(size)
    , mMaxLongSize(longSize)
    , mLongSkipCount(longSkipCount)
    , mInfoStr(info)
    , mId(0)
    , mLongId(0)
{
}

CImageBuffer::CRingBuffer::~CRingBuffer()
{
    std::lock_guard<std::mutex> lock(mMutex);
    int initCount = mList.size() - 1;
    for (int i = initCount; i < initCount - NAlgorithms::IAlertAlgorithm::sMinAlgoFrameCount; i--)
    {
        if (i >= 0)
        {
            mList[i]->decreaseRefCounter();
        }
    }
}

bool CImageBuffer::CRingBuffer::isFull() const
{
    return mList.size() >= mMaxSize;
}

void CImageBuffer::CRingBuffer::push_back(const pMatWithTimeStamp elem)
{
    std::lock_guard<std::mutex> lock(mMutex);
    mList.push_back(elem);

    if (mList.size() > mMaxSize)
    {
       mList.front()->decreaseRefCounter();

       if ((mMaxLongSize > 0 && (mLongSkipCount > 0) && (mLongId++ %mLongSkipCount == 0))
           || mLongList.size() < mMaxLongSize)
       {
          mLongList.push_back(mList.front());
          if (mLongList.size() > mMaxLongSize)
          {
             mLongList.pop_front();
          }
       }
       mList.pop_front();
    }

    static const int sOffset = 1;
    if (mList.size() > (NAlgorithms::IAlertAlgorithm::sMinAlgoFrameCount + sOffset))
    {
       //delete data for less mem ussage
       mList[mList.size() - (NAlgorithms::IAlertAlgorithm::sMinAlgoFrameCount  + sOffset)]->decreaseRefCounter();
    }
}

int CImageBuffer::CRingBuffer::capacity() const
{
    return mMaxSize;
}

bool CImageBuffer::CRingBuffer::empty() const
{
    return mList.empty();
}

void CImageBuffer::CRingBuffer::clear()
{
    std::lock_guard<std::mutex> lock(mMutex);
    mList.clear();
    mLongList.clear();
}

int CImageBuffer::CRingBuffer::size() const
{
    return mList.size();
}

int CImageBuffer::CRingBuffer::longSize() const
{
    return mLongList.size();
}

size_t CImageBuffer::CRingBuffer::getNextId()
{
    return mId++;
}

void CImageBuffer::CRingBuffer::setHasAlert(bool alertStatus)
{
    mIsHasAlert = alertStatus;
    if (alertStatus)
    {
        mLastAlertDt = QDateTime::currentDateTime();
    }
}

bool CImageBuffer::CRingBuffer::getHasAlert() const
{
    return mIsHasAlert;
}

const QDateTime&CImageBuffer::CRingBuffer::getLastAlertDt() const
{
    return mLastAlertDt;
}

const QList<pMatWithTimeStamp>& CImageBuffer::CRingBuffer::getList() const
{
    std::lock_guard<std::mutex> lock(mMutex);
    return mList;
}

const pMatWithTimeStamp CImageBuffer::CRingBuffer::operator[](int elementId) const
{
    std::lock_guard<std::mutex> lock(mMutex);
    if (elementId < 0 || elementId >= mList.size())
    {
       return nullptr;
    }
    return mList.at(elementId);
}

const std::string& CImageBuffer::CRingBuffer::getInfo() const
{
    return mInfoStr;
}

CImageBuffer::CRingBuffer::CRingBuffer(const CImageBuffer::CRingBuffer& other)
{
std::lock_guard<std::mutex> lock(mMutex);
    if (this != &other)
    {
#define COPY(field) field = other.field
        COPY(mList);
        COPY(mLongList);
        COPY(mMaxSize);
        COPY(mMaxLongSize);
        COPY(mLongSkipCount);
        COPY(mInfoStr);
        COPY(mId);
        COPY(mLongId);
    }

    int initCount = mList.size() - 1;
    for (int i = initCount; i < initCount - NAlgorithms::IAlertAlgorithm::sMinAlgoFrameCount; i--)
    {
        if (i >= 0)
        {
            mList[i]->increaseRefCounter();
        }
    }
}

void CImageBuffer::CRingBuffer::setInfoStr(const std::string& infoStr)
{
    mInfoStr = infoStr;
}

const QList<pMatWithTimeStamp>& CImageBuffer::CRingBuffer::getLongList() const
{
    std::lock_guard<std::mutex> lock(mMutex);
    return mLongList;
}
