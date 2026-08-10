package hu.szigyi.nested.hierarchical.graph.util;

import hu.szigyi.nested.hierarchical.graph.domain.generated.org.graphdrawing.graphml.xmlns.GraphmlType;
import hu.szigyi.nested.hierarchical.graph.domain.generated.org.graphdrawing.graphml.xmlns.ObjectFactory;

import java.io.IOException;
import java.io.InputStream;
import java.net.URL;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBElement;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Unmarshaller;

public class GraphMLUtil {

	public GraphmlType readGraphML(final String path) throws JAXBException {
		final URL resource = this.getClass().getResource(path);

		try (InputStream stream = resource.openStream()) {
			final JAXBContext jaxbContext = JAXBContext.newInstance(ObjectFactory.class);

			final Unmarshaller jaxbUnmarshaller = jaxbContext.createUnmarshaller();
			final JAXBElement<GraphmlType> jaxbElement = (JAXBElement<GraphmlType>) jaxbUnmarshaller.unmarshal(stream);
			final GraphmlType graphml = jaxbElement.getValue();
			System.out.println("Graph: " + graphml.getGraphOrData());
			return graphml;
		} catch (final IOException e) {
			e.printStackTrace();
			throw new RuntimeException(e);
		}
	}
}
