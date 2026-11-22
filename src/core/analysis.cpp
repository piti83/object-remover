#include "object_remover/analysis.hpp"

namespace object_remover {

std::vector<Object> analyse(const cv::Mat& /*mask*/, int /*connectivity*/) {
    // TODO: implement with cv::connectedComponentsWithStats.
    return {};
}

}  // namespace object_remover
