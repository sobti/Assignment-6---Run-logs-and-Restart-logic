// graphql function doesn't throw an error so we have to check to check for the result.errors to throw manually
const wrapper = promise =>
  promise.then(result => {
    if (result.errors) throw result.errors;
    return result;
  });

exports.createPages = async ({ graphql, actions }) => {
  const { createPage } = actions;
  const result = await wrapper(
    graphql(`
      {
        allPrismicProject {
          nodes {
            uid
          }
        }
        allPrismicPost {
          nodes {
            uid
          }
        }
      }
    `)
  );

  const projectTemplate = require.resolve('./src/templates/project.jsx');
  const postTemplate = require.resolve('./src/templates/post.jsx');
  const { nodes: projectNodes } = result.data.allPrismicProject;
  const { nodes: postNodes } = result.data.allPrismicPost;

  projectNodes.forEach(node => {
    createPage({
      path: `/work/${node.uid}`,
      component: projectTemplate,
      context: {
        uid: node.uid,
      },
    });
  });

  postNodes.forEach(node => {
    createPage({
      path: `/blog/${node.uid}`,
      component: postTemplate,
      context: {
        uid: node.uid,
      },
    });
  });
};
