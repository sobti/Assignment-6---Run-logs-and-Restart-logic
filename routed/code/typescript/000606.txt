import { Test, TestingModule } from '@nestjs/testing';
import { ChaiController } from './chais.controller';

describe('ChaiController', () => {
  let controller: ChaiController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [ChaiController],
    }).compile();

    controller = module.get<ChaiController>(ChaiController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
