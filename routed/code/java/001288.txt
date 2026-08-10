import java.util.Date;

import org.junit.Test;
import org.sdmlib.models.classes.Card;
import org.sdmlib.models.classes.ClassModel;
import org.sdmlib.models.classes.Clazz;
import org.sdmlib.models.classes.DataType;

public class modelgen {
	@Test
	public void genhmsModel() {
		ClassModel model = new ClassModel();
		Clazz hmsModel = model.createClazz("HMSModel");
		hmsModel.withAttribute("id", DataType.INT);
		hmsModel.withAttribute("modTime", DataType.ref(Date.class));
		
		Clazz role = model.createClazz("Role");
		hmsModel.withAttribute("value", DataType.STRING);
				
		Clazz user = model.createClazz("User");
		user.withSuperClazz(hmsModel);
		user.withAttribute("email", DataType.STRING);
		user.withAttribute("firstName", DataType.STRING);
		user.withAttribute("lastName", DataType.STRING);
		user.withAttribute("password", DataType.STRING);
		user.withAttribute("matrikelNumber", DataType.STRING);
		user.withAttribute("lastLogin", DataType.ref(Date.class));
		user.withAttribute("emailValidated", DataType.STRING);
		
		user.withAssoc(role, "role", Card.MANY);
		
		Clazz lecture = model.createClazz("Lecture");
		lecture.withSuperClazz(hmsModel);
		lecture.withAttribute("name", DataType.STRING);
		lecture.withAttribute("description", DataType.STRING);
		lecture.withAttribute("questionsDuty ???", DataType.STRING); // ???
		lecture.withAttribute("closingdate", DataType.ref(Date.class));
		lecture.withAttribute("optionalDuties", DataType.INT);
		lecture.withAttribute("lowerProcentualBounderyOfDuties", DataType.INT);
		lecture.withAttribute("minimumPercentageForExamination", DataType.INT);
		
		Clazz semester = model.createClazz("Semester");
		semester.withSuperClazz(hmsModel);
		semester.withAttribute("semester", DataType.STRING);
		semester.withAssoc(lecture, "lectures", Card.MANY, "semester", Card.ONE);

		// Message
		Clazz message = model.createClazz("Message");
		message.withSuperClazz(hmsModel);
		message.withAttribute("body", DataType.STRING);
		message.withAttribute("date", DataType.ref(Date.class));
		message.withAssoc(hmsModel, "parent", Card.ONE);
//		message.withAttribute("parent", DataType.ref(hmsModel));
		message.withAssoc(user, "sender", Card.ONE, "messages",Card.MANY);
		
		model.dumpHTML("model");
	}
}
