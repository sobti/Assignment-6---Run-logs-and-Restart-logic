#ifndef SLIDER_H
#define SLIDER_H

#include<QSlider>
#include<QMouseEvent>
#include<QEvent>
#include <QLabel>
#include "MyToolTip.h"

//滑动条
class CMySlider : public QSlider
{
    Q_OBJECT
public:
    explicit CMySlider(Qt::Orientation orientation, QWidget* parent =0);
    void    mouseMoveEvent(QMouseEvent* event);
    void    mousePressEvent(QMouseEvent * event);
    void    mouseReleaseEvent(QMouseEvent *event);
    bool    event(QEvent *event);
    bool    eventFilter(QObject* target, QEvent * event);  //事件过滤
    void    leaveEvent(QEvent *event);
    void    enterEvent(QEvent *event);

signals:
    void    signalPressPosition(qint64 position);
    void    signalMouseMovePosition(qint64 position);


public slots:
    void    slotSliderPressed();
    void    slotSliderReleased();

public:
    void    setToolTipText(const QString toolTip);
    CMyToolTip* getToolTip();
    void    setToolTipVisible(bool bIsToolTipVisible);
    bool    getToolTipVisible();

private:
    bool    m_bIsLeftPressDown;
    bool    m_bIsSliderPressed;
    bool    m_bIsDragSlider;

    qint64  m_pressedPosition;
    qint64  m_LeftPressPointX;
    qint64  m_mouseMovePointX;

    CMyToolTip*  m_toolTip;
    bool        m_bIsToolTipVisible;

};

#endif // SLIDER_H
