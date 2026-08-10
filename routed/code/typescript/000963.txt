import { DataPointHandler } from './dataPointHandler';
import * as $ from 'jquery';
import * as SVG from 'svg.js';

/**
 * The class that moves and animates images.
 */
export class AnimationHandler {

  // the model which we need a reference to in order to pause, resume, and stop it
  cupCounterModel: object;

  // handles the temperature data points that are displayed and sent to WISE
  dataPointHandler: object;

  // keeps track of the time in integer seconds
  time: number;

  /**
   * Constructor that sets up event listeners.
   * @param cupCounterModel The cup counter model.
   */
  constructor(cupCounterModel: object) {
    this.time = 0;
    this.cupCounterModel = cupCounterModel;
    this.dataPointHandler = new DataPointHandler();
    this.cupMovementAnimation = null;
    this.heatAnimations = [];
    this.draw = SVG('modelDiv').size(260, 200);
    this.createCup();
    this.createCounter();
    this.createCupThermometer();
    this.createCounterThermometer();
    this.createThermometerTemperatureMarks();
    this.createDoneMessage();
  }

  /**
   * Create the cup which consists of the handle, the warm cup, the hot cup,
   * the hot cup mask, and the cup temperature display.
   */
  createCup() {
    let cupX = 50;
    let cupY = 70;
    let cupHandleX = cupX - 22;
    let cupHandleY = cupY + 3;
    this.cupHandle = this.draw.image('./images/cupHandle.svg').move(cupHandleX, cupHandleY);
    this.cupWarm = this.draw.image('./images/cupWarm.svg').move(cupX, cupY);
    this.cupHot = this.draw.image('./images/cupHot.svg').move(cupX, cupY);

    // create the text that displays the temperature on the cup
    let cupTemperatureDisplayX = cupX + 12;
    let cupTemperatureDisplayY = cupY + 10;
    this.cupTemperatureDisplay = this.draw.text('60\u00B0C')
        .move(cupTemperatureDisplayX, cupTemperatureDisplayY);
    this.cupTemperatureDisplay.font(this.getFontObject(16));

    /*
     * Create the hot cup mask that we will use to slowly wipe away the hot cup
     * which will then reveal the warm cup.
     */
    let cupMaskGradient = this.draw.gradient('linear', (stop) => {
      stop.at(0, 'white')
      stop.at(0.9, 'white')
      stop.at(1, 'black')
    }).rotate(90);
    this.cupMaskRectStartingX = cupX;
    this.cupMaskRectStartingY = cupY;
    this.cupMaskRect = this.draw.rect(62, 44).fill(cupMaskGradient)
        .move(this.cupMaskRectStartingX, this.cupMaskRectStartingY);
    this.cupMask = this.draw.mask().add(this.cupMaskRect);
    this.cupHot.maskWith(this.cupMask);

    /*
     * Put all the elements into a group so that we can move them all at once
     * when we lower the cup.
     */
    this.cupGroup = this.draw.group();
    this.cupGroup.add(this.cupHandle);
    this.cupGroup.add(this.cupWarm);
    this.cupGroup.add(this.cupHot);
    this.cupGroup.add(this.cupTemperatureDisplay);
    this.cupGroupStartingX = this.cupGroup.x();
    this.cupGroupStartingY = this.cupGroup.y();
  }

  /**
   * Create the counter which consists of the warm counter, the hot counter, the
   * hot counter mask, and the counter temperature display.
   */
  createCounter() {
    let counterX = 42;
    let counterY = 120;
    this.counterWarm = this.draw.image('./images/counterWarm.svg')
        .move(counterX, 120);
    this.counterCold = this.draw.image('./images/counterCold.svg')
        .move(counterX, 120);

    // create the text that displays the temperature on the counter
    let counterTemperatureDisplayX = counterX + 20;
    let counterTemperatureDisplayY = counterY + 16;
    this.counterTemperatureDisplay = this.draw.text('20\u00B0C')
        .move(counterTemperatureDisplayX, counterTemperatureDisplayY);
    this.counterTemperatureDisplay.font(this.getFontObject(16));

    /*
     * Create the cold counter mask that we will use to slowly wipe away the
     * cold counter which will then reveal the warm counter.
     */
    let counterGradient = this.draw.gradient('linear', (stop) => {
      stop.at(0, 'black')
      stop.at(0.1, 'white')
      stop.at(1, 'white')
    }).rotate(90);
    this.counterMaskRectStartingX = counterX;
    this.counterMaskRectStartingY = counterY - 6;
    this.counterMaskRect = this.draw.rect(80, 80).fill(counterGradient)
        .move(this.counterMaskRectStartingX, this.counterMaskRectStartingY);
    this.counterCold.maskWith(this.counterMaskRect);
  }

  /**
   * Create the cup thermometer which consists of the thermometer, the red
   * mercury, the mercury mask, and the text label.
   */
  createCupThermometer() {
    let cupThermometerX = 140;
    let cupThermometerY = 70;

    // the text label above the Cup thermometer
    let cupThermometerTextX = cupThermometerX;
    let cupThermometerTextY = cupThermometerY - 14;
    this.cupThermometerText = this.draw.text('Cup');
    this.cupThermometerText.move(cupThermometerTextX, cupThermometerTextY);
    this.cupThermometerText.font(this.getFontObject(14));

    // the mercury
    let cupThermometerRedBarX = cupThermometerX + 8;
    let cupThermometerRedBarY = cupThermometerY + 3;
    this.cupThermometerRedBar = this.draw.image('./images/thermometerRedBar.svg')
        .move(cupThermometerRedBarX, cupThermometerRedBarY);

    // the thermometer
    this.cupThermometer = this.draw.image('./images/thermometer.svg')
        .move(cupThermometerX, cupThermometerY);

    /*
     * The mask for the mercury that we will use to change the height of the
     * mercury.
     */
    this.cupThermometerMaskRectStartingX = cupThermometerX + 7;
    this.cupThermometerMaskRectStartingY = cupThermometerY + 5;
    this.cupThermometerMaskRect = this.draw.rect(9, 70).fill('white')
        .move(this.cupThermometerMaskRectStartingX, this.cupThermometerMaskRectStartingY);
    this.cupThermometerMask = this.draw.mask().add(this.cupThermometerMaskRect);
    this.cupThermometerRedBar.maskWith(this.cupThermometerMask);
  }

  /**
   * Create the counter thermometer which consists of the thermometer, the red
   * mercury, the mercury mask, and the text label.
   */
  createCounterThermometer() {
    let counterThermometerX = 200;
    let counterThermometerY = 70;

    // the text label above the counter thermometer
    let counterThermometerTextX = counterThermometerX - 10;
    let counterThermometerTextY = counterThermometerY - 14;
    this.counterThermometerText = this.draw.text('Counter');
    this.counterThermometerText.move(counterThermometerTextX, counterThermometerTextY);
    this.counterThermometerText.font(this.getFontObject(14));

    // the mercury
    let counterThermometerRedBarX = counterThermometerX + 8;
    let counterThermometerRedBarY = counterThermometerY + 3;
    this.counterThermometerRedBar = this.draw.image('./images/thermometerRedBar.svg')
        .move(counterThermometerRedBarX, counterThermometerRedBarY);

    // the thermometer
    this.counterThermometer = this.draw.image('./images/thermometer.svg')
        .move(counterThermometerX, counterThermometerY);

    /*
     * The mask for the mercury that we will use to change the height of the
     * mercury.
     */
    this.counterThermometerMaskRectStartingX = counterThermometerX + 7;
    this.counterThermometerMaskRectStartingY = counterThermometerY + 68;
    this.counterThermometerMaskRect = this.draw.rect(9, 70).fill('white')
        .move(this.counterThermometerMaskRectStartingX, this.counterThermometerMaskRectStartingY);
    this.counterThermometerMask = this.draw.mask().add(this.counterThermometerMaskRect);
    this.counterThermometerRedBar.maskWith(this.counterThermometerMask);
  }

  /**
   * Create the temperature markings for the thermometers that looks like
   * - 60°C -
   * - 50°C -
   * - 40°C -
   * - 30°C -
   * - 20°C -
   */
  createThermometerTemperatureMarks() {
    let text = ' - 60\u00B0C - \n - 50\u00B0C -  \n - 40\u00B0C -  \n - 30\u00B0C -  \n - 20\u00B0C - ';
    this.temperatureLabels = this.draw.text(text);
    this.temperatureLabels.move(162, 70);
    this.temperatureLabels.font(this.getFontObject(12));
  }

  /**
   * The done message that we will display when the simulation completes
   * running.
   */
  createDoneMessage() {
    this.doneText = this.draw.text('Done!');
    this.doneText.move(160, 25);
    this.doneText.font(this.getFontObject(16));
    this.doneText.hide();
  }

  /**
   * Get an object that contains specifications for a font.
   * @param size The font size.
   * @return A object containing font attributes.
   */
  getFontObject(size) {
    return { size: size, family: 'Times New Roman' };
  }

  /**
   * Start the animation that lowers the cup onto the counter.
   */
  startCupLowering() {
    this.dataPointHandler.initializeTrial();

    // send the initial temperature data points to WISE
    this.updateTemperatures();

    this.cupMovementAnimation = this.cupGroup.animate(1000).move(0, 12).after(() => {
      this.startHeatTransfer();
    });
  }

  /**
   * Generate a function that scales the cup position.
   */
  generateCupThermometerEasingFunction() {
    let thisDataPointHandler = this.dataPointHandler;
    return (pos) => {
      return thisDataPointHandler.getScaledCupPos(pos);
    };
  }

  /**
   * Generate a function that scales the counter position.
   */
  generateCounterThermometerEasingFunction() {
    let thisDataPointHandler = this.dataPointHandler;
    return (pos) => {
      return thisDataPointHandler.getScaledCounterPos(pos);
    };
  }

  /**
   * Start the heat transfer animation on the cup and counter.
   */
  startHeatTransfer() {
    // animate the heat on the cup, counter, and thermometers
    let animationDurationSeconds = 15;
    let animationDurationMilliseconds = animationDurationSeconds * 1000;
    this.cupHeatAnimation = this.cupMaskRect
        .animate(animationDurationMilliseconds).move(this.cupMaskRectStartingX, 18);
    this.counterHeatAnimation = this.counterMaskRect
        .animate(animationDurationMilliseconds).move(this.counterMaskRectStartingX, 170);
    this.cupThermometerAnimation = this.cupThermometerMaskRect
        .animate(animationDurationMilliseconds,
            this.generateCupThermometerEasingFunction()).move(147, 122);
    this.counterThermometerAnimation = this.counterThermometerMaskRect
        .animate(animationDurationMilliseconds,
            this.generateCounterThermometerEasingFunction()).move(207, 122);

    /*
     * This array will be used to hold all the animations associated with the
     * heat transfer. We will use it for pausing and resuming.
     */
    this.heatAnimations = [];
    this.heatAnimations.push(this.cupHeatAnimation);
    this.heatAnimations.push(this.counterHeatAnimation);
    this.heatAnimations.push(this.cupThermometerAnimation);
    this.heatAnimations.push(this.counterThermometerAnimation);

    /*
     * Add a callback after each second so we can update the temperatures and
     * send them to WISE. The way this works is that the cupHeatAnimation.once()
     * takes in a value from 0 to 1 where 0 represents the beginning of its
     * animation and 1 represents the end of its animation. We split up this
     * total animation time into 15 segments. Note that 1/15 = 0.0625.
     * Therefore we are calling
     * this.cupHeatAnimation.once(0)
     * this.cupHeatAnimation.once(0.0625)
     * this.cupHeatAnimation.once(0.1333)
     * this.cupHeatAnimation.once(0.2)
     * this.cupHeatAnimation.once(0.2666)
     * this.cupHeatAnimation.once(0.3333)
     * ...
     * this.cupHeatAnimation.once(1)
     */
    for (let t = 0; t <= animationDurationSeconds; t++) {
      this.cupHeatAnimation.once(t * (1/animationDurationSeconds), () => {
        this.incrementTimeCounter();

        /*
         * Update the temperature displays and also send the temperatures to
         * WISE.
         */
        this.updateTemperatures();
      });
    }

    this.cupHeatAnimation.after(() => {
      // the animation has completed so we will tell the model we are done
      this.cupCounterModel.setCompleted();
    });
  }

  /**
   * Update the temperatures on the display and send them to WISE.
   */
  updateTemperatures() {
    // send the updated trial to WISE
    this.dataPointHandler.updateAndSendTrial(this.getTimeCounter());

    // update the temperatures displayed on the cup and counter
    let time = this.getTimeCounter();
    let cupTemperature = this.dataPointHandler.getCupTemperature(time);
    let counterTemperature = this.dataPointHandler.getCounterTemperature(time);
    this.setCupTemperatureReadout(cupTemperature);
    this.setCounterTemperatureReadout(counterTemperature);
  }

  /**
   * Get the current time in the model.
   * @return An integer representing the amount of time the model has been
   * running. The value will be between 0-15 inclusive.
   */
  getTimeCounter() {
    return this.time;
  }

  /**
   * Increment the model timer by 1 second.
   */
  incrementTimeCounter() {
    this.time += 1;
  }

  /**
   * Set the model timer back to 0 seconds.
   */
  resetTimeCounter() {
    this.time = 0;
  }

  /**
   * Pause all the elements in the model.
   */
  pause() {
    if (this.heatAnimations.length == 0) {
      // we are in the cup movement phase
      this.cupMovementAnimation.pause();
    } else {
      // we are in the heat transfer phase
      for (let animation of this.heatAnimations) {
        animation.pause();
      }
    }
  }

  /**
   * Resume animating all the elements in the model.
   */
  resume() {
    if (this.heatAnimations.length == 0) {
      // we are in the cup movement phase
      this.cupMovementAnimation.play();
    } else {
      // we are in the heat transfer phase
      for (let animation of this.heatAnimations) {
        animation.play();
      }
    }
  }

  /**
   * Stop all the animations which consist of the cup movement animation,
   * heat transfer animations, and thermometer animations.
   */
  stopAnimations() {
    if (this.cupMovementAnimation != null) {
      this.cupMovementAnimation.stop();
    }
    for (let animation of this.heatAnimations) {
      animation.stop();
    }
  }

  /**
   * Reset all the elements back to their original positions and states.
   */
  resetAnimations() {

    // set the time back to 0
    this.resetTimeCounter();

    // reset all the animations
    this.resetCupPosition();
    this.resetCupHeatMask();
    this.resetCounterHeatMask();
    this.resetCupThermometerMask();
    this.resetCounterThermometerMask();
    this.hideDoneMessage();

    /*
     * Set the cup and counter temperature displays back to their starting
     * temperatures.
     */
    let time = this.getTimeCounter();
    this.setCupTemperatureReadout(this.dataPointHandler.getCupTemperature(time));
    this.setCounterTemperatureReadout(this.dataPointHandler.getCounterTemperature(time));
  }

  /**
   * Set the cup back to its starting position.
   */
  resetCupPosition() {
    this.cupGroup.move(this.cupGroupStartingX, this.cupGroupStartingY);
  }

  /**
   * Set the cup heat mask back to its starting position so that the hot cup
   * is fully displayed.
   */
  resetCupHeatMask() {
    this.cupMaskRect
        .move(this.cupMaskRectStartingX, this.cupMaskRectStartingY);
  }

  /**
   * Set the counter heat mask back to its starting position so that the cold
   * counter is fully displayed.
   */
  resetCounterHeatMask() {
    this.counterMaskRect
        .move(this.counterMaskRectStartingX, this.counterMaskRectStartingY);
  }

  /**
   * Set the cup thermometer mask back to its starting position so that the
   * thermometer is at 60C.
   */
  resetCupThermometerMask() {
    this.cupThermometerMaskRect
        .move(this.cupThermometerMaskRectStartingX, this.cupThermometerMaskRectStartingY);
  }

  /**
   * Set the counter thermometer mask back to its starting position so that the
   * thermometer is at 20C.
   */
  resetCounterThermometerMask() {
    this.counterThermometerMaskRect
        .move(this.counterThermometerMaskRectStartingX, this.counterThermometerMaskRectStartingY);
  }

  /**
   * Set the cup temperature that is displayed on the cup.
   */
  setCupTemperatureReadout(temp) {
    this.cupTemperatureDisplay.text(Math.floor(temp) + '\u00B0C');
  }

  /**
   * Set the counter temperature that is displayed on the counter.
   */
  setCounterTemperatureReadout(temp) {
    this.counterTemperatureDisplay.text(Math.floor(temp) + '\u00B0C');
  }

  /**
   * The model is done running.
   */
  modelCompleted() {
    this.showDoneMessage();
  }

  showDoneMessage() {
    this.doneText.show();
  }

  hideDoneMessage() {
    this.doneText.hide();
  }
}
