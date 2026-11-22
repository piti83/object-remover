#include "object_remover/segmentation.hpp"

namespace object_remover {

cv::Mat segment(const cv::Mat& bgr) {
    // TODO: implement. Dummy: empty mask of the same size.
    return cv::Mat::zeros(bgr.size(), CV_8UC1);
}

}  // namespace object_remover
