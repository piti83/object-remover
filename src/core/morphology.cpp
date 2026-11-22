#include "object_remover/morphology.hpp"

namespace object_remover {

cv::Mat areaOpening(const cv::Mat& mask, int /*minArea*/, int /*connectivity*/) {
    // TODO: implement (union-find or BFS per component).
    return mask.clone();
}

cv::Mat reconstruct(const cv::Mat& /*marker*/, const cv::Mat& mask) {
    // TODO: implement (iterated geodesic dilation until stable).
    return mask.clone();
}

cv::Mat openingByReconstruction(const cv::Mat& mask, const cv::Mat& /*se*/) {
    // TODO: implement (erode, then reconstruct).
    return mask.clone();
}

cv::Mat fillHoles(const cv::Mat& mask) {
    // TODO: implement (reconstruct complement from the border).
    return mask.clone();
}

}  // namespace object_remover
